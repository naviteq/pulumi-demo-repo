import pulumi_aws as aws
import pulumi

# Retrieve configuration values from Pulumi configuration
config_rds = pulumi.Config("pulumi-dev-env")
allocated_storage = config_rds.require_int("rds-allocated_storage")
storage_type = config_rds.require("rds-storage_type")
engine = config_rds.require("rds-engine")
engine_version = config_rds.require("rds-engine_version")
instance_class = config_rds.require("rds-instance_class")
parameter_group_name = config_rds.require("rds-parameter_group_name")
password = config_rds.require_secret("rds-password")
username = config_rds.require_secret("username")

def create_rds_security_group(vpc_id):
    rds_sg = aws.ec2.SecurityGroup("pulumi-rds-sg",
                                   vpc_id=vpc_id,
                                   description="Allow inbound traffic for RDS",
                                   egress=[{
                                       'protocol': '-1',
                                       'from_port': 0,
                                       'to_port': 0,
                                       'cidr_blocks': ['0.0.0.0/0'],
                                   }],
                                   ingress=[{
                                       'protocol': 'tcp',
                                       'from_port': 3306,
                                       'to_port': 3306,
                                       'cidr_blocks': ['10.0.3.0/24', '10.0.4.0/24', '10.0.5.0/24'],
                                   }],
                                   tags={
                                       'Name': 'pulumi-rds-sg',
                                       'ManagedBy': 'Pulumi',
                                   })
    return rds_sg


def create_rds_subnet_group(private_subnets):
    subnet_ids = [subnet.id for subnet in private_subnets]
    rds_subnet_group = aws.rds.SubnetGroup("pulumi-rds-subnet-group",
                                           subnet_ids=subnet_ids,
                                           tags={
                                               'Name': 'pulumi-rds-subnet-group',
                                               'ManagedBy': 'Pulumi'
                                           })
    return rds_subnet_group


def create_rds_instance(vpc_id, rds_subnet_group):
    rds_sg = create_rds_security_group(vpc_id)
    rds_instance = aws.rds.Instance("pulumi-rds-instance",
                                    db_name="pulumi_created_db",
                                    allocated_storage=allocated_storage,
                                    storage_type=storage_type,
                                    engine=engine,
                                    db_subnet_group_name=rds_subnet_group.name,
                                    deletion_protection=True, ## Pulumi will not be able to delete rds instance when you run pulumi destroy, need to modify it first and remove deletion_protection
                                    publicly_accessible=False,
                                    vpc_security_group_ids=[rds_sg.id],
                                    multi_az=False,
                                    engine_version=engine_version,
                                    instance_class=instance_class,
                                    parameter_group_name=parameter_group_name,
                                    password=password,
                                    skip_final_snapshot=True,
                                    auto_minor_version_upgrade=True,
                                    tags={
                                        'Name': 'pulumi-rds-db',
                                        'Environment': 'dev',
                                        'ManagedBy': 'Pulumi',
                                    },
                                    username=username)

    return rds_instance
