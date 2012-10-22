
from boto.ec2.autoscale import AutoScaleConnection
from boto.ec2.autoscale import LaunchConfiguration
from boto.ec2.autoscale import AutoScalingGroup
from boto.ec2.autoscale import ScalingPolicy
from boto.ec2.cloudwatch import MetricAlarm

import boto.ec2.autoscale

import aws_common

#=============#
#= Constants =#
#=============#

SECURITY_GROUP = '12_LP1_SEC_D7001D_nicnys-8'
AMI = 'ami-c7a8a8b3'
KEY = '12_LP1_KEY_D7001D_nicnys-8'
AUTOSCALING_GROUP = 'nicnys-8-requestHandler-as-eu'
LAUNCH_CONFIGURATION = 'nicnys-8-requestHandler-lc-eu'
REGION = 'eu-west-1'
AVAILABILITY_ZONE = 'eu-west-1b'


#===============#
#= Autoscaling =#
#===============#

#eu_region = None
#for region in regions(aws_access_key_id=aws_common.AWS_ACCESS_KEY,
#                      aws_secret_access_key=aws_common.AWS_SECRET_KEY):
#    #for region in regions():
#    if region.name == REGION:
#		eu_region = region
#		break
#
#print eu_region

asConnection = boto.ec2.autoscale.connect_to_region(REGION)


    #AutoScaleConnection(aws_access_key_id=aws_common.AWS_ACCESS_KEY,
    #                               aws_secret_access_key=aws_common.AWS_SECRET_KEY,
# region=eu_region)

print asConnection


# Create a launch configuration; the set of information needed
# by the autoscale group to launch new instances
lc = LaunchConfiguration(
    name = LAUNCH_CONFIGURATION,
    image_id = AMI,
    key_name = KEY,
    security_groups = [SECURITY_GROUP])

print lc

asConnection.create_launch_configuration(lc)

# Create an autoscale group associated with the launch configuration
ag = AutoScalingGroup(
    group_name = AUTOSCALING_GROUP,
    availability_zones = [AVAILABILITY_ZONE],
    launch_config = lc,
    min_size = 1, max_size = 5,
    connection = asConnection)

print ag

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

alarm_dimensions = { "QueueName" : "12_LP1_SQS_D7001D_jimnys-8_frontend-in" }

# Create a new instance if the existing cluster
# averages more than 70% CPU for two minutes
scale_up_alarm = MetricAlarm(
    name = 'Scale up when number of messages on queue is high',
    namespace= ' AWS/SQS',
    metric = 'ApproximateNumberOfMessagesVisible',
    statistic = 'Average',
    comparison = '>', threshold = 10,
    period = 60, evaluation_periods = 1,
    alarm_actions = [scale_up_policy.policy_arn],
    dimensions = alarm_dimensions)

cloudwatch.create_alarm(scale_up_alarm)

# Terminate an instance if the existing cluster
# averages less than 40% CPU for two minutes
scale_down_alarm = MetricAlarm(
    name = 'Scale down when number of messages on queue is low',
    namespace = 'AWS/SQS',
    metric = 'ApproximateNumberOfMessagesVisible',
    statistic = 'Average',
    comparison = '<', threshold = 2,
    period = '60', evaluation_periods = 1,
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
