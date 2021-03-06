import boto.ec2.elb
from boto.ec2.elb import HealthCheck

from boto.ec2.autoscale import AutoScaleConnection
from boto.ec2.autoscale import LaunchConfiguration
from boto.ec2.autoscale import AutoScalingGroup
from boto.ec2.autoscale import ScalingPolicy
from boto.ec2.cloudwatch import MetricAlarm
from boto.ec2.autoscale import Tag

#=============#
#= Constants =#
#=============#

SECURITY_GROUP = '12_LP1_SEC_D7001D_nicnys-8'
AMI = 'ami-6995951d'
KEY = '12_LP1_KEY_D7001D_nicnys-8'
AUTOSCALING_GROUP = 'nicnys-8-sensorDataHandler-as'
INSTANCE_NAME = 'nicnys-8-sensorDataHandler-ec2'
LAUNCH_CONFIGURATION = 'nicnys-8-sensorDataHandler-lc'
LOAD_BALANCER = 'nicnys-8-sensorDataHandler-lb'
REGION = 'eu-west-1'
AVAILABILITY_ZONES = ['eu-west-1b']

INSTANCE_PORT = 9999
LOAD_BALANCER_PORT = 12345

#=======================#
#== Load balancinging ==#
#=======================#

lb_connection = boto.ec2.elb.connect_to_region(REGION)

# Periodically check that TCP connections can be made to all instanes
hc = HealthCheck(
    # Seconds between each check:
    interval = 20,
    # Consecutive failed checks before an instance is deemed dead:
    healthy_threshold = 3,
    # Seconds the loadbalancer will wait for a check:
    unhealthy_threshold = 5, 
    target = 'TCP:' + str(INSTANCE_PORT))

# If there already exists a loadbalancer, use it
try:
    lb_list = lb_connection.get_all_load_balancers(load_balancer_names=[LOAD_BALANCER])
    lb = lb_list[0]

# Otherwise, create a new one
except:

    # Listen to traffic on port 9999, forward to port 9999 on the instances
    ports = [(LOAD_BALANCER_PORT, INSTANCE_PORT, 'tcp')]
    lb = lb_connection.create_load_balancer(LOAD_BALANCER, AVAILABILITY_ZONES, ports)

"""

# We assume that the loadbalancer already exists
lb_list = lb_connection.get_all_load_balancers(load_balancer_names=[LOAD_BALANCER])
lb = lb_list[0]

lb.configure_health_check(hc)

dnsName = lb.dns_name
print("URL: " + dnsName)
"""
#=================#
#== Autoscaling ==#
#=================#

#========#
#= Tags =#
#========#

as_connection = boto.ec2.autoscale.connect_to_region(REGION)

# create a tag for the austoscale group
name_tag = Tag(key='Name', value = INSTANCE_NAME, propagate_at_launch=True, resource_id=AUTOSCALING_GROUP)
course_tag = Tag(key='course', value = 'D7001D', propagate_at_launch=True, resource_id=AUTOSCALING_GROUP)
user_tag = Tag(key='user', value = 'nicnys-8', propagate_at_launch=True, resource_id=AUTOSCALING_GROUP)

# Add the tag to the autoscale group
as_connection.create_or_update_tags([name_tag, course_tag, user_tag])

# If there is no launch configuration, create it
configurations = as_connection.get_all_launch_configurations(names=[LAUNCH_CONFIGURATION])
if (configurations == []):
    lc=LaunchConfiguration(
        name=LAUNCH_CONFIGURATION,
        image_id=AMI,
        key_name=KEY,
        security_groups=[SECURITY_GROUP])

    as_connection.create_launch_configuration(lc)
    
# Otherwise, use the existing one
else:
    lc = configurations[0]

# Create a new autoscaling group if it doesn't already exist
my_groups = as_connection.get_all_groups(names=[AUTOSCALING_GROUP])
if (my_groups == []):
    ag=AutoScalingGroup(
    group_name=AUTOSCALING_GROUP,
    load_balancers=[LOAD_BALANCER],
    availability_zones=AVAILABILITY_ZONES,
    launch_config=lc,
    min_size=2,
    max_size=4,
    connection=as_connection)

    as_connection.create_auto_scaling_group(ag)
    
else:
    ag = my_groups[0]

#====================#
#= Scaling policies =#
#====================#
# The scaling policies tell us *how* to scale

scale_up_policy = ScalingPolicy(
    name='scale_up',
    adjustment_type='ChangeInCapacity',
    as_name=AUTOSCALING_GROUP,
    scaling_adjustment=1,
    cooldown=180)

scale_down_policy = ScalingPolicy(
    name='scale_down',
    adjustment_type='ChangeInCapacity',
    as_name=AUTOSCALING_GROUP,
    scaling_adjustment=-1,
    cooldown=180)

# Submit policies to AWS
as_connection.create_scaling_policy(scale_up_policy)
as_connection.create_scaling_policy(scale_down_policy)

# The polices now have extra properties that aren't
# accessible locally. Refresh the policies by requesting
# them back again.
scale_up_policy = as_connection.get_all_policies(
    as_group=AUTOSCALING_GROUP,
    policy_names=['scale_up'])[0]

scale_down_policy = as_connection.get_all_policies(
    as_group=AUTOSCALING_GROUP,
    policy_names=['scale_down'])[0]


#=====================#
#= Cloudwatch alarms =#
#=====================#

#The cloudwatch alarms tell us *when* to scale

cloudwatch = boto.ec2.cloudwatch.connect_to_region(REGION)

alarm_dimensions = {"AutoScalingGroupName": AUTOSCALING_GROUP}

# Create a new instance if the existing cluster
# averages more than 60% CPU for one minute
scale_up_alarm = MetricAlarm(
    name='scale_up_on_cpu', 
    namespace='AWS/EC2',
    metric='CPUUtilization', 
    statistic='Average',
    comparison='>', 
    threshold='40',
    period='60', 
    evaluation_periods=1,
    alarm_actions=[scale_up_policy.policy_arn],
    dimensions=alarm_dimensions)

cloudwatch.create_alarm(scale_up_alarm)

# Terminate an instance if the existing cluster
# averages less than 10% CPU for two minutes
scale_down_alarm = MetricAlarm(
        name='scale_down_on_cpu', 
        namespace='AWS/EC2',
        metric='CPUUtilization', 
        statistic='Average',
        comparison='<', 
        threshold='20',
        period='60', 
        evaluation_periods=1,
        alarm_actions=[scale_down_policy.policy_arn],
        dimensions=alarm_dimensions)

cloudwatch.create_alarm(scale_down_alarm)

"""
def stop_autoscaling():
    ag.shutdown_instances()
    ag.delete()
"""




