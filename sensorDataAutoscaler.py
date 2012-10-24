from sys import argv, exit
import boto.ec2.elb
import boto.ec2.autoscale
import time

from boto.ec2.elb import HealthCheck
from boto.ec2.autoscale import LaunchConfiguration
from boto.ec2.autoscale import AutoScalingGroup
from boto.ec2.autoscale import ScalingPolicy
from boto.ec2.cloudwatch import MetricAlarm
from boto.ec2.autoscale import Tag
from datetime import datetime

# PREDETERMINED VALUES

region = 'eu-west-1'
zones = ['eu-west-1a', 'eu-west-1b']
image_id = 'ami-6995951d'
autoscaling_group = 'nicnys-8-sensorDataHandler-as'
key_name = '12_LP1_KEY_D7001D_nicnys-8'
lc_name     = 'nicnys-8-sensorDataHandler-lc'
asg_name    = 'nicnys-8-sensorDataHandler-as'
sec_group   = '12_LP1_SEC_D7001D_nicnys-8'
instance_name = 'nicnys-8-sensorDataHandler-ec2'
security_group = '12_LP1_SEC_D7001D_nicnys-8'
load_balancer = 'nicnys-8-sensorDataHandler-lb'

instance_port = 9999
load_balancer_port = 12345

min_instances = 2
max_instances = 5


def launchLoadBalancing():
        connection = boto.ec2.elb.connect_to_region(region)
        
        # Periodically check that TCP connections can be made to all instanes
        hc = HealthCheck(
            # Seconds between each check:
            interval = 20,
            # Consecutive failed checks before an instance is deemed dead:
            healthy_threshold = 3,
            # Seconds the loadbalancer will wait for a check:
            unhealthy_threshold = 5, 
            target = 'TCP:' + str(instance_port))

        # If there already exists a loadbalancer, use it
        try:
            lb_list = connection.get_all_load_balancers(
                    load_balancer_names=[load_balancer])
            
            lb = lb_list[0]

        # Otherwise, create a new one
        except:
            # Listen to traffic on port 9999, forward to port 9999 on the instances
            ports = [(load_balancer_port, instance_port, 'tcp')]
            lb = connection.create_load_balancer(
                    load_balancer, zones, ports)


def launchAutoScale():
    print "Connecting to region: " + region
    connection = boto.ec2.autoscale.connect_to_region(region)

    print 'Creating launch configuration: ' + lc_name
    lc = LaunchConfiguration(
        name=lc_name, 
        image_id=image_id,
        key_name=key_name,
                security_groups = [security_group])

    connection.create_launch_configuration(lc)
    print 'Done. LaunchConfiguration created.'

    print 'Creating AutoScalingGroup: ' + asg_name
    asg = AutoScalingGroup(
        group_name=asg_name,
                load_balancers = [load_balancer],
        availability_zones=zones,
        launch_config=lc, 
        min_size=min_instances, 
        max_size=max_instances,
        connection=connection)

    connection.create_auto_scaling_group(asg)
    print 'Done. AutoScalingGroup created.'

    # create a tag for the austoscale group
    print 'Creating tags for instances:'
    name_tag = Tag(key='Name', value = instance_name, propagate_at_launch=True, resource_id=asg_name)
    course_tag = Tag(key='Course', value = 'D7001D', propagate_at_launch=True, resource_id=asg_name)
    user_tag = Tag(key='User', value = 'nicnys-8', propagate_at_launch=True, resource_id=asg_name)

    # Add the tag to the autoscale group
    connection.create_or_update_tags([name_tag, course_tag, user_tag])
    print "Done. Tags added."

    # Set local scale properties.
    print 'Creating scale up/down policy'
    scale_up_policy = ScalingPolicy(
        name='scale_up', 
        adjustment_type='ChangeInCapacity',
        as_name=asg_name, 
        scaling_adjustment=1, 
        cooldown=180)

    scale_down_policy = ScalingPolicy(
        name='scale_down',
        adjustment_type='ChangeInCapacity',
        as_name=asg_name, 
        scaling_adjustment=-1, 
        cooldown=180)

    # Push them to AWS.
    connection.create_scaling_policy(scale_up_policy)
    connection.create_scaling_policy(scale_down_policy)
    print 'Done. Scaling policies created.'

    # Get extra properties from AWS.
    scale_up_policy = connection.get_all_policies(as_group=asg_name, policy_names=['scale_up'])[0]
    scale_down_policy = connection.get_all_policies(as_group=asg_name, policy_names=['scale_down'])[0]

    print 'Setting up alarms...'
    cloudwatch = boto.ec2.cloudwatch.connect_to_region(region_name=region)

    alarm_dimensions = {"AutoScalingGroupName": autoscaling_group}
    print 'ScaleUpAlarm'
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

    print 'ScaleDownAlarm'
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
    print 'Finished'

def shutdown():
    print 'Shutdown:'
    connection = boto.ec2.autoscale.connect_to_region(region)

    # scaling policies
    try:
        policies = connection.get_all_policies(as_group=asg_name)
        for p in policies:
            print 'Deleting policy.'
            p.delete
    except Exception:
        print 'AutoScalingGroup ' + asg_name + ' doesn\'t exist.'

    # autoscaling group
    
    try:
        asg = connection.get_all_groups(names=[asg_name])[0]
        print 'Deleting AutoScalingGroup: ' + asg_name
        asg.delete(force_delete=True)
    except Exception:
        print 'AutoScalingGroup ' + asg_name + ' doesn\'t exist.'

    # launch configuration
    try:
        lc = connection.get_all_launch_configurations(names=[lc_name])[0]
        print 'Deleting launch configuration: ' + lc_name
        lc.delete()
    except Exception:
        print 'LaunchConfiguration ' + lc_name + ' doesn\'t exist.'

    # cloudwatch alarms
    try:
        cloudwatch = boto.ec2.cloudwatch.connect_to_region(region_name=region)
        cloudwatch.delete_alarms([alarm_up_name, alarm_down_name])
        print 'Deleting CloudWatch alarms...'
    except Exception:
        print 'CloudWatchAlarms doesn\'t exist'

    print 'Shutdown complete.'

if __name__ == "__main__":
    if len(argv) == 1:
                launchLoadBalancing()
                launchAutoScale()   
    elif len(argv) == 2 and argv[1] == '--shutdown':
        shutdown()
    else:
        exit('usage: %s [--shutdown]' % argv[0])
