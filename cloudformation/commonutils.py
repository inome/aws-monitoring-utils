__author__ = 'dkonidena'

'''Return the shard number given the coretype, instance number and the shardtype.
   The following topology is used for people and locations:

    instance1 - leader:shard0, replica:shard3
    instance2 - leader:shard1, replica:shard4
    instance3 - leader:shard2, replica:shard0
    instance4 - leader:shard3, replica:shard5
    instance5 - leader:shard4, replica:shard1
    instance6 - leader:shard5, replica:shard2
'''
def get_shard_num(coretype,instance,shardtype):
    if coretype == 'helix-people' or coretype == 'helix-locations':

        #get the proper leader and replica shards
        if shardtype == 'leader':
            if instance == 1:
                return str(0)
            elif instance == 2:
                return str(1)
            elif instance == 3:
                return str(2)
            elif instance == 4:
                return str(3)
            elif instance == 5:
                return str(4)
            elif instance == 6:
                return str(5)
            else:
                raise Exception("invalid instance value: only [1,6] are permitted")
        elif shardtype == 'replica':
            if instance == 1:
                return str(3)
            elif instance == 2:
                return str(4)
            elif instance == 3:
                return str(0)
            elif instance == 4:
                return str(5)
            elif instance == 5:
                return str(1)
            elif instance == 6:
                return str(2)
            else:
                raise Exception("invalid instance value: only [1,6] are permitted")

    elif coretype == 'helix-organizations':
        if shardtype == 'leader':
            return str(0)
        elif shardtype == 'replica':
            return str(0)
        else:
            raise Exception("Unknown shard type. Accepted shardtype values: [leader, replica]")
    else:
        raise Exception("Unknown coretype. Accepted values: [helix-people, helix-locations, helix-organizations]")


'''get the complete s3 location of the shard given the base s3location, coretype,
instance and shardtype'''
def get_shard_location(s3location,coretype,instance,shardtype):
    prefix = str()

    if coretype == 'helix-people' or coretype == 'helix-locations':

        #set the right s3 location prefix
        if coretype == 'helix-people':
            prefix = '/people'
        elif coretype == 'helix-locations':
            prefix = '/locations'

    elif coretype == 'helix-organizations':
        prefix = '/organizations'
    else:
        raise Exception("Unknown coretype. Accepted values: [helix-people, helix-locations, helix-organizations]")

    return s3location + prefix + '/zipped/SHARD' + get_shard_num(coretype,instance,shardtype) + '.tar.gz'


'''Return the proper invocation script given coretype, instance num, and shard type '''
def get_solr_setup_invocation(coretype,instance_num,shardtype):
    if coretype == 'helix-people' or coretype == 'helix-locations':
        if shardtype == 'leader':
            actual_shard_num = get_shard_num(coretype,instance_num,"leader")
            shard_num = int(get_shard_num(coretype,instance_num,"leader")) + 1
            core_node = shard_num
            num_shards = 6
            return "bash -x setup_solr.sh leader" + " " + actual_shard_num + " " + str(num_shards) + " " + "SHARD" + actual_shard_num + " " + "shard" + str(shard_num) + " " + coretype + " " + "core_node" + str(core_node)
        elif shardtype == 'replica':
            actual_shard_num = get_shard_num(coretype,instance_num,"replica")
            shard_num = int(get_shard_num(coretype,instance_num,"replica")) + 1
            core_node = 6 + shard_num
            num_shards = 6
            return "bash -x setup_solr.sh replica" + " " + actual_shard_num + " " + str(num_shards) + " " + "SHARD" + actual_shard_num + " " + "shard" + str(shard_num) + " " + coretype + " " + "core_node" + str(core_node)
    elif coretype == 'helix-organizations':
        return "bash -x setup_solr.sh leader 0 1 SHARD0 shard1 helix-organizations core_node0"



'''Given a deployment type (dev/prod) and a core type, get the instance name to be used during
the setup '''
def get_instance_name(coretype, deployment="dev"):
    if coretype == 'helix-people':
        if deployment == 'dev':
            return "solrcloud-people-dev"
        elif deployment == 'prod':
            return "solrcloud-people-prod"
        else:
            raise Exception("Unknown deployment. Accepted values: [dev,prod]")

    elif coretype == 'helix-locations':
        if deployment == 'dev':
            return "solrcloud-locations-dev"
        elif deployment == 'prod':
            return "solrcloud-locations-prod"
        else:
            raise Exception("Unknown deployment. Accepted values: [dev,prod]")

    elif coretype == 'helix-organizations':
        if deployment == 'dev':
            return "solrcloud-organizations-dev"
        elif deployment == 'prod':
            return "solrcloud-organizations-prod"
        else:
            raise Exception("Unknown deployment. Accepted values: [dev,prod]")
    else:
        raise Exception("Unknown coretype. Accepted values: [helix-people, helix-locations, helix-organizations]")


'''Given a coretype, return the config name used by Zookeeper in identifying the appropriate
solr core'''
def get_solr_config_name(coretype):
    if coretype == 'helix-people':
        return "personcore"

    elif coretype == 'helix-locations':
        return "locationcore"

    elif coretype == 'helix-organizations':
        return "organizationcore"
    else:
        raise Exception("Unknown coretype. Accepted values: [helix-people, helix-locations, helix-organizations]")
