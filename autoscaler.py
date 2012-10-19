import boto.ec2.elb
from boto.ec2.elb import HealthCheck

from boto.ec2.autoscale import AutoScaleConnection
from boto.ec2.autoscale import LaunchConfiguration
from boto.ec2.autoscale import AutoScalingGroup
from boto.ec2.autoscale import ScalingPolicy
from boto.ec2.cloudwatch import MetricAlarm

#=============#
#= Constants =#
#=============#

SECURITY_GROUP = '12_LP1_SEC_D7001D_nicnys-8'
AMI = 'ami-5f02022b'
KEY = '12_LP1_KEY_D7001D_nicnys-8'
AUTOSCALING_GROUP = 'nicnys-8-sensorServer-as'
LAUNCH_CONFIGURATION = 'nicnys-8-sensorServer-lc'
LOAD_BALANCER = 'nicnys-8-sensorServer-lb'
REGION = 'eu-west-1'
AVAILABILITY_ZONE = 'eu-west-1b'

INSTANCE_PORT = 9999
LOAD_BALANCER_PORT = 9999

#=====================#
#= Load balancinging =#
#=====================#

lbConnection = boto.ec2.elb.connect_to_region(REGION)

# Periodically check that TCP connections can be made to all instanes
hc = HealthCheck(
    # Seconds between each check:
    interval = 20,
    # Consecutive failed checks before an instance is deemed dead:
    healthy_threshold = 3,
    # Seconds the loadbalancer will wait for a check:
    unhealthy_threshold = 5, 
    target = 'TCP:' + str(INSTANCE_PORT))

# Listen to traffic on port 9999, forward to port 9999 on the instances
ports = [(LOAD_BALANCER_PORT, INSTANCE_PORT, 'tcp')]

# The crap below might want a *list* of availability zones?
lb = lbConnection.create_load_balancer(LOAD_BALANCER, AVAILABILITY_ZONE, ports)
lb.configure_health_check(hc)

dnsName = lb.dns_name
print("URL: " + dnsName)


#===============#
#= Autoscaling =#
#===============#

asConnection = boto.ec2.autoscale.connect_to_region(REGION)

# Create a launch configuration; the set of information needed
# by the autoscale group to launch new instances
lc = LaunchConfiguration(
    name = LAUNCH_CONFIGURATION, image_id = AMI,
    key_name = KEY,
    security_groups = [SECURITY_GROUP])

# Create an autoscale group associated with the launch configuration
ag = AutoScalingGroup(
    group_name = AUTOSCALING_GROUP,
    load_balancers = [LOAD_BALANCER],
    availability_zones = [AVAILABILITY_ZONE],
    launch_config = lc,
    min_size = 1, max_size = 2,
    connection = asConnection)

asConnection.create_auto_scaling_group(ag)


#====================#
#= Scaling policies =#
#====================#

# The scaling policies tell us *how* to scale

scale_up_policy = ScalingPolicy(
    name = 'scale_up', adjustment_type = 'ChangeInCapacity',
    as_name = AUTOSCALING_GROUP, scaling_adjustment = 1, cooldown = 180)

scale_down_policy = ScalingPolicy(
    name='scale_down', adjustment_type='ChangeInCapacity',
    as_name = AUTOSCALING_GROUP, scaling_adjustment = -1, cooldown = 180)

# Submit policies to AWS
asConnection.create_scaling_policy(scale_up_policy)
asConnection.create_scaling_policy(scale_down_policy)

# The polices now have extra properties that aren't
# accessible locally. Refresh the policies by requesting
# them back again.
scale_up_policy = asConnection.get_all_policies(
    as_group = AUTOSCALING_GROUP, policy_names = ['scale_up'])[0]

scale_down_policy = asConnection.get_all_policies(
    as_group = AUTOSCALING_GROUP, policy_names = ['scale_down'])[0]


#=====================#
#= Cloudwatch alarms =#
#=====================#

#The cloudwatch alarms tell us *when* to scale

cloudwatch = boto.ec2.cloudwatch.connect_to_region(REGION)

alarm_dimensions = {"AutoScalingGroupName": AUTOSCALING_GROUP}

# Create a new instance if the existing cluster
# averages more than 70% CPU for two minutes
scale_up_alarm = MetricAlarm(
    name = 'scale_up_on_cpu', namespace= ' AWS/EC2',
    metric = 'CPUUtilization', statistic = 'Average',
    comparison = '>', threshold = '70',
    period = '60', evaluation_periods = 2,
    alarm_actions = [scale_up_policy.policy_arn],
    dimensions = alarm_dimensions)

cloudwatch.create_alarm(scale_up_alarm)

# Terminate an instance if the existing cluster
# averages less than 40% CPU for two minutes
scale_down_alarm = MetricAlarm(
    name = 'scale_down_on_cpu', namespace = 'AWS/EC2',
    metric = 'CPUUtilization', statistic = 'Average',
    comparison = '<', threshold = '40',
    period = '60', evaluation_periods = 2,
    alarm_actions = [scale_down_policy.policy_arn],
    dimensions = alarm_dimensions)

cloudwatch.create_alarm(scale_down_alarm)


"""
#=========================================#
#= Just some stuff I want to remember... =#
#=========================================#


ag = asConnection.get_all_groups(names=['nicnys-8-sensorServer-as'])[0]
[i.instance_id for i in ag.instances]

ag.shutdown_instances()
ag.delete()

"""
