import pulumi
import pulumi_aws as aws


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
                                   tags={'Name': 'pulumi-rds-sg'})
    return rds_sg


def create_rds_subnet_group(private_subnets):
    subnet_ids = [subnet.id for subnet in private_subnets]
    rds_subnet_group = aws.rds.SubnetGroup("pulumi-rds-subnet-group",
                                           subnet_ids=subnet_ids,
                                           tags={'Name': 'pulumi-rds-subnet-group'})
    return rds_subnet_group


def create_rds_instance(vpc_id, rds_subnet_group):
    rds_sg = create_rds_security_group(vpc_id)
    rds_instance = aws.rds.Instance("default",
                                    name="pulumi_created_db",
                                    allocated_storage=10,
                                    storage_type="gp3",
                                    db_name="mydb",
                                    engine="mysql",
                                    db_subnet_group_name=rds_subnet_group.name,
                                    deletion_protection=True,
                                    publicly_accessible=False,
                                    vpc_security_group_ids=[rds_sg.id],
                                    multi_az=False,
                                    engine_version="8.0.33",
                                    instance_class="db.t3.micro",
                                    parameter_group_name="default.mysql5.7",
                                    password="foobarbaz",
                                    skip_final_snapshot=True,
                                    auto_minor_version_upgrade=True,
                                    username="foo")