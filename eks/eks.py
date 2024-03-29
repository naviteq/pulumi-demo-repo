import pulumi
import pulumi_eks as eks
import pulumi_aws as aws
from iam.iam import create_eks_worker_role

# Retrieve configuration values from Pulumi configuration
config_eks = pulumi.Config("pulumi-dev-env")
eks_instance_type = config_eks.require("eks-cluster_instance_type")
eks_cluster_version = config_eks.require("eks-cluster_version")
eks_cluster_name = config_eks.require("eks-cluster_name")
eks_capacity_type = config_eks.require("eks-capacity-type")
eks_node_disk_size = config_eks.require("eks-node-disk-size")


# Create an EKS cluster
def create_eks_cluster(private_subnets, public_subnets, vpc_id):
    eks_work_role_object = create_eks_worker_role()
    eks_cluster = eks.Cluster(eks_cluster_name,
                              vpc_id=vpc_id,
                              name=eks_cluster_name,
                              private_subnet_ids=[subnet.id for subnet in private_subnets],
                              public_subnet_ids=[subnet.id for subnet in public_subnets],
                              skip_default_node_group=True,
                              endpoint_public_access=True,
                              version=eks_cluster_version,
                              instance_role=eks_work_role_object,
                              role_mappings=[
                                  {
                                      'groups': ['system:bootstrappers', 'system:nodes'],
                                      'rolearn': eks_work_role_object.arn,
                                      'username': 'system:node:{{EC2PrivateDNSName}}',
                                  }
                              ],
                              # vpc_cni_options=eks.VpcCniOptionsArgs(
                              #     warm_ip_target=5,
                              # ),
                              enabled_cluster_log_types=[
                                  "api",
                                  "audit",
                                  "authenticator"],
                              tags={
                                  'Name': f'{eks_cluster_name}',
                                  'ManagedBy': 'Pulumi',
                                  'Environment': 'dev',
                              })

    # Define Managed Node Group
    # noinspection PyTypeChecker
    managed_node_group = eks.ManagedNodeGroup(
        "managed-node-group",
        cluster=eks_cluster,
        node_role=eks_work_role_object,
        subnet_ids=[subnet.id for subnet in private_subnets],
        capacity_type=eks_capacity_type,
        disk_size=eks_node_disk_size,
        scaling_config=aws.eks.NodeGroupScalingConfigArgs(
            desired_size=3,
            min_size=1,
            max_size=3,
        ),
        instance_types=[eks_instance_type],
        tags={
            'Name': f'{eks_cluster_name}',
            'ManagedBy': 'Pulumi',
            'Environment': 'dev',
        },
    )

    # Deploy EKS addons after cluster creation
    deploy_eks_addons(eks_cluster)

    # Output the cluster's kubeconfig and name.
    pulumi.export("kubeconfig", eks_cluster.kubeconfig)
    pulumi.export('cluster-name', eks_cluster.eks_cluster.name)

    return eks_cluster, eks_cluster.kubeconfig


# Func to deploy addons to EKS
def deploy_eks_addons(eks_cluster):
    addons = [
        {
            "name": "vpc-cni",
            "addon_version": "v1.16.3-eksbuild.2",
            "resolve_conflicts_on_create": "OVERWRITE",
        },
        {
            "name": "kube-proxy",
            "addon_version": "v1.29.1-eksbuild.2",
            "resolve_conflicts_on_create": "OVERWRITE",
        },
        {
            "name": "coredns",
            "addon_version": "v1.11.1-eksbuild.6",
            "resolve_conflicts_on_create": "OVERWRITE",
        },
        {
            "name": "aws-ebs-csi-driver",
            "addon_version": "v1.28.0-eksbuild.1",
            "resolve_conflicts_on_create": "OVERWRITE",
        },
        {
            "name": "aws-efs-csi-driver",
            "addon_version": "v1.7.5-eksbuild.2",
            "resolve_conflicts_on_create": "OVERWRITE",
        },

    ]

    for addon in addons:
        addon_name = addon["name"]
        aws.eks.Addon(addon_name,
                      cluster_name=eks_cluster.name,
                      addon_name=addon_name,
                      addon_version=addon["addon_version"],
                      resolve_conflicts_on_create=addon.get("resolve_conflicts_on_create", "NONE"),
                      opts=pulumi.ResourceOptions(depends_on=[eks_cluster]))
