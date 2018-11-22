#!/usr/bin/env python3

import argparse
import os
from sssweep import *
from taskrun import *


def main(args):
  ##############################################################################
  # setup
  cpus = os.cpu_count()
  all_mem = MemoryResource.current_available_memory_gib()
  rm = ResourceManager(CounterResource('cpus', 9999, cpus),
                       MemoryResource('mem', 9999, all_mem))
  vob = VerboseObserver(description=False, log=args.log)
  cob = FileCleanupObserver()
  fm = (FailureMode.AGGRESSIVE_FAIL if args.fail_fast else
        FailureMode.ACTIVE_CONTINUE)
  tm = TaskManager(observers=[vob, cob],
                   resource_manager=rm,
                   failure_mode=fm)

  supersim_path = 'supersim'
  settings_path = 'settings_realistic_dfly.json'
  ssparse_path = '~/supersim/ssparse/bin/ssparse'
  transient_path = '~/supersim/ssparse/scripts/transient.py'

  def create_task(tm, name, cmd, console_out, task_type, config):
    task = ProcessTask(tm, name, cmd)
    if console_out:
      task.stdout_file = console_out
      task.stderr_file = console_out
    if task_type is 'sim':
      task.resources = {'cpus': 1, 'mem': args.memory}
    else:
      task.resources = {'cpus': 1, 'mem': (all_mem / cpus) * 0.99}
    return task

  sw = Sweeper(supersim_path, settings_path,
               ssparse_path, transient_path,
               create_task, args.directory,
               parse_scalar=0.001, latency_units='ns',
               viewer='dev')
  ##############################################################################
  # simulation variables
  topology_routing = [#'Dragonfly-adaptive-33x1-8x1-4-5v',
                      #'Dragonfly-adaptivePar-33x1-8x1-4-5v',
                      #'Dragonfly-adaptiveValn-33x1-8x1-4-5v',
                      'Dragonfly-adaptiveParValn-33x1-8x1-4-5v']

  def set_topolgy_routing(ra, config):
    loc = 'network.protocol_classes[0].routing'
    cmd = ('{0}.output_type=string=vc '
           '{0}.max_outputs=uint=1 '
           '{0}.output_algorithm=string=random '
           .format(loc))

    # parsing topology setup
    topo = ra.split('-')[0]
    routing = ra.split('-')[1]
    # topology
    if topo == 'HyperX':
      widths = ra.split('-')[2].replace("x", ",")
      weights = ra.split('-')[3].replace("x", ",")
      con = ra.split('-')[4]
      vcs = ra.split('-')[5].replace("v", "")
      cmd += ('network.topology=string=hyperx '
              'network.dimension_widths=uint=[{0}] '
              'network.dimension_weights=uint=[{1}] '
              'network.concentration=uint={2} '
              'network.protocol_classes[0].num_vcs=uint={3} '
              .format(widths, weights, con, vcs))
    elif topo == 'Dragonfly':
      g_width = ra.split('-')[2].split('x')[0]
      g_weight = ra.split('-')[2].split('x')[1]
      l_width = ra.split('-')[3].split('x')[0]
      l_weight = ra.split('-')[3].split('x')[1]
      con = ra.split('-')[4]
      vcs = ra.split('-')[5].replace("v", "")
      cmd += ('network.topology=string=dragonfly '
              'network.global_width=uint={0} '
              'network.global_weight=uint={1} '
              'network.local_width=uint={2} '
              'network.local_weight=uint={3} '
              'network.concentration=uint={4} '
              'network.protocol_classes[0].num_vcs=uint={5} '
              .format(g_width, g_weight, l_width, l_weight, con, vcs))
    elif topo == 'FatTree':
      vcs = ra.split('-')[4].replace("v", "")
      cmd += ('network.topology=string=fat_tree '
              'network.down_up=uint=[] '
              'network.protocol_classes[0].num_vcs=uint={0} '
              .format(vcs))
      # level parsing
      num_levels = ra.split('-')[2].replace("l", "")
      for l in range(int(num_levels)):
        info_level = ra.split('-')[3].split('X')[l].replace("x",",")
        cmd += ('network.down_up[{0}]=uint=[{1}] '.format(l, info_level))
    else:
      assert False

    # routing
    cmd += ('{0}.mode=string=vc '
            '{0}.reduction.max_outputs=uint=1 '.format(loc))
    # dragonfly
    if routing == 'minimal' and topo == 'Dragonfly':
      cmd += ('{0}.algorithm=string=minimal '
              '{0}.randomized_global=bool=false '
              '{0}.reduction.algorithm=string=all_minimal '
              .format(loc))
    elif routing == 'minimalRandomGlobal' and topo == 'Dragonfly':
      cmd += ('{0}.algorithm=string=minimal '
              '{0}.randomized_global=bool=true '
              '{0}.reduction.algorithm=string=all_minimal '
              .format(loc))
    elif routing == 'adaptive' and topo == 'Dragonfly':
      cmd += ('{0}.algorithm=string=adaptive '
              '{0}.progressive_adaptive=bool=false '
              '{0}.valiant_node=bool=false '
              '{0}.reduction.algorithm=string=weighted '
              .format(loc))
    elif routing == 'adaptivePar' and topo == 'Dragonfly':
      cmd += ('{0}.algorithm=string=adaptive '
              '{0}.progressive_adaptive=bool=true '
              '{0}.valiant_node=bool=false '
              '{0}.reduction.algorithm=string=weighted '
              .format(loc))
    elif routing == 'adaptiveValn' and topo == 'Dragonfly':
      cmd += ('{0}.algorithm=string=adaptive '
              '{0}.progressive_adaptive=bool=false '
              '{0}.valiant_node=bool=true '
              '{0}.reduction.algorithm=string=weighted '
              .format(loc))
    elif routing == 'adaptiveParValn' and topo == 'Dragonfly':
      cmd += ('{0}.algorithm=string=adaptive '
              '{0}.progressive_adaptive=bool=true '
              '{0}.valiant_node=bool=true '
              '{0}.reduction.algorithm=string=weighted '
              .format(loc))
    # fattree
    elif routing == 'deterministic' and topo == 'FatTree':
      cmd += ('{0}.algorithm=string=common_ancestor '
              '{0}.least_common_ancestor=bool=true '
              '{0}.deterministic=bool=true '
              '{0}.reduction.algorithm=string=all_minimal '
              .format(loc))
    elif routing == 'oblivious' and topo == 'FatTree':
      cmd += ('{0}.algorithm=string=common_ancestor '
              '{0}.least_common_ancestor=bool=true '
              '{0}.deterministic=bool=false '
              '{0}.reduction.algorithm=string=all_minimal '
              .format(loc))
    elif routing == 'adaptive' and topo == 'FatTree':
      cmd += ('{0}.algorithm=string=common_ancestor '
              '{0}.least_common_ancestor=bool=true '
              '{0}.deterministic=bool=false '
              '{0}.reduction.algorithm=string=least_congested_minimal '
              .format(loc))
    # hyperx
    elif routing in ['DDAL', 'VDAL', 'DOAL'] and topo == 'HyperX':
      adtypes = {'DDAL': 'dimension_adaptive',
                 'VDAL': 'variable',
                 'DOAL': 'dimension_order'}
      cmd += ('{0}.algorithm=string=dal '
              '{0}.adaptivity_type=string={1} '
              '{0}.max_deroutes=uint=2 '  # VDAL: vcs =  dims  + DR_allowed
              '{0}.multi_deroute=bool=false '  # VDAL only
              '{0}.decision_scheme=string=monolithic_weighted '
              .format(loc, adtypes[routing]))
    elif routing == 'UGAL' and topo == 'HyperX':
      cmd += ('{0}.algorithm=string=ugal '
              '{0}.minimal=string=dimension_order '
              '{0}.non_minimal=string=valiants '
              '{0}.intermediate_node=string=regular '
              '{0}.first_hop_multi_port=bool=false '
              '{0}.short_cut=bool=true '
              '{0}.min_all_vc_sets=bool=false '
              '{0}.decision_scheme=string=monolithic_weighted '
              .format(loc))
    elif routing == 'UGAL+' and topo == 'HyperX':
      cmd += ('{0}.algorithm=string=ugal '
              '{0}.minimal=string=dimension_order '
              '{0}.non_minimal=string=valiants '
              '{0}.intermediate_node=string=unaligned '
              '{0}.first_hop_multi_port=bool=false '
              '{0}.short_cut=bool=true '
              '{0}.min_all_vc_sets=bool=false '
              '{0}.decision_scheme=string=monolithic_weighted '
              .format(loc))
    elif routing == 'DOR' and topo == 'HyperX':
      cmd += ('{0}.algorithm=string=dimension_order '
              .format(loc))
    elif routing == 'VAL' and topo == 'HyperX':
      cmd += ('{0}.algorithm=string=valiants '
              '{0}.minimal=string=dimension_order '
              '{0}.non_minimal=string=valiants '
              '{0}.intermediate_node=string=regular '
              '{0}.short_cut=bool=true '
              .format(loc))
    else:
      assert False
    return cmd
  sw.add_variable('Topology Routing', 'TR', topology_routing,
                  set_topolgy_routing)

  variable_channels = ['scalar-[2.93_4.25]', 'fixed-[9_99]'] # 64x1-8x2-8c
  #'scalar-[1.28_8.36]', 'fixed-[9_99]'] # 32x4-16x1-8c


  def set_channels(chan, config):
    ch_mode = chan.split('-')[0]
    ch_value = chan.split('-')[1]
    # channel latency
    cmd = ' network.channel_mode=string='+ ch_mode
    # fixed
    if ch_mode == 'fixed':
      for item in config:
        if item['name'] == 'Topology Routing':
          if 'HyperX' in item['value']:
            cmd += ' network.internal_channel.latency=uint='+ ch_value
          elif 'Dragonfly' in item['value']:
            ch_value = ch_value.replace("[","")
            ch_value = ch_value.replace("]","")
            local_latency = ch_value.split('_')[0]
            global_latency = ch_value.split('_')[1]
            cmd += ' network.local_channel.latency=uint='+ local_latency
            cmd += ' network.global_channel.latency=uint='+ global_latency
    # scalar
    elif ch_mode == 'scalar':
      for item in config:
        if item['name'] == 'Topology Routing':
          if item['value'].split('-')[0] == 'HyperX':
            ch_value = ch_value.replace("_",",")
            cmd += ' network.channel_scalars=float='+ ch_value
          elif item['value'].split('-')[0] == 'Dragonfly':
            ch_value = ch_value.replace("[","")
            ch_value = ch_value.replace("]","")
            local_scalar = ch_value.split('_')[0]
            global_scalar = ch_value.split('_')[1]
            cmd += ' network.local_scalar=float='+ local_scalar
            cmd += ' network.global_scalar=float='+ global_scalar
          else:
            assert False
    return cmd
  sw.add_variable('Channels', 'Ch', variable_channels, set_channels)

  tailor_buffers = [#'fixed-589', 'tailored-2.2',
                    ##'tailored-3.0', 'tailored-4.0',
                    'tailored-5.0']
                    ##'tailored-7.5',
                    #'tailored-10.0'] #'tailored-20.0',
                    #'tailored-201.0']
  def set_tailored_buffers(buff, config):
    input_queue_max = '589'
    input_queue_min = '16'
    bf_mode = buff.split('-')[0]
    bf_value = buff.split('-')[1]
    cmd = ' network.router.input_queue_mode=string='+ bf_mode
    cmd += ' network.router.input_queue_min=uint='+ input_queue_min
    cmd += ' network.router.input_queue_max=uint='+ input_queue_max
    # buffer length
    if bf_mode == 'fixed':
      cmd += ' network.router.input_queue_depth=uint='+ bf_value
    elif bf_mode == 'tailored':
      cmd += ' network.router.input_queue_depth=float='+ bf_value
    else:
      print('Buffer mode not valid')
    cmd += (' init_credits_mode=ref=network.router.input_queue_mode '
            ' init_credits=ref=network.router.input_queue_depth '
            ' credits_max=ref=network.router.input_queue_max '
            ' credits_min=ref=network.router.input_queue_min ')
    return cmd
  sw.add_variable('Tailored Buffers', 'TB', tailor_buffers, set_tailored_buffers)

  cong_sensor = ['normalized_vc'] # ['absolute_vc',
  def set_congestion_sensor(congS, config):
    cmd = 'network.router.congestion_sensor.mode=string='+ congS
    return cmd
  sw.add_variable('Congestion Sensor', 'CS', cong_sensor, set_congestion_sensor)

  congestion_mode = {'OD':'output_and_downstream'} #'output', 'downstream']
  def set_congestion_mode(congM, config):
    return 'network.router.congestion_mode=string='+ congestion_mode[congM]
  sw.add_variable('Congestion Mode', 'CM', congestion_mode, set_congestion_mode)

  bias_modes = ['regular']#, 'bimodal']
  def set_bias_mode(bm, config):
    return ('network.protocol_classes[0].routing.bias_mode=string={} '
            .format(bm))
  sw.add_variable('Bias Mode', 'BM', bias_modes, set_bias_mode);

  hop_count_modes = ['normalized']#, 'absolute']
  def set_hop_count_mode(hcm, config):
    return ('network.protocol_classes[0].routing.hop_count_mode=string={} '
            .format(hcm))
  sw.add_variable('Hop Count Mode', 'HCM', hop_count_modes, set_hop_count_mode)

  congestion_offsets = [0.1] #0.0, 0.1, 0.2]
  def set_congestion_offset(offset, config):
    return ('network.router.congestion_sensor.offset=float={} '.format(offset))
  sw.add_variable('Congestion Offset', 'CO', congestion_offsets,
                  set_congestion_offset)

  traffic_patterns = {'UR': 'uniform_random',
                      'GA-half': 'group_attack',
                      'GA-opposite': 'group_attack'}
  def set_traffic_pattern(tp, config):
    # topology needs to be matched!
    loc = 'workload.applications[0].blast_terminal.traffic_pattern'
    cmd = ('{0}.type=string={1} '.format(loc, traffic_patterns[tp]))
    if tp.startswith('URB'):
      dimIdx = {'x': 0, 'y': 1, 'z': 2}[tp[-1]]
      cmd += ('{0}.enabled_dimensions[{1}]=bool=true '.format(loc, dimIdx))
    elif tp == 'S2':
      cmd += ('{0}.enabled_dimensions[0]=bool=true '
              '{0}.enabled_dimensions[1]=bool=true '.format(loc))
    elif tp.startswith('GA'):
      ga_type = tp.split('-')[1]
      if (len(ga_type) > 1):
        # string
        cmd += ('{0}.group_size=ref=network.local_width '
                '{0}.concentration=ref=network.concentration '
                '{0}.destination_mode=string=random '
                '{0}.group_mode=string={1} '
                .format(loc, ga_type))
      else:
        # int
        cmd += ('{0}.group_size=ref=network.local_width '
                '{0}.concentration=ref=network.concentration '
                '{0}.destination_mode=string=random '
                '{0}.group_mode=uint={1} '
                .format(loc, ga_type))
    return cmd
  sw.add_variable('Traffic Pattern', 'TP', traffic_patterns,
                  set_traffic_pattern, compare=False)


  congestion_bias = [0.1] #, 0.0, 0.2]
  def set_congestion_bias(cbias, config):
    loc = 'network.protocol_classes[0].routing'
    ibias = 0.0
    cmd = ''
    for item in config:
      if item['name'] == 'Topology Routing':
        if 'HyperX' in item['value']:
          # hyperx
          cmd = ('{0}.congestion_bias=float={1} '
                 '{0}.independent_bias=float={2} '
                 .format(loc, cbias, ibias))
        elif 'FatTree' not in item['value']:
          # reduction
          cmd = ('{0}.reduction.congestion_bias=float={1} '
                 '{0}.reduction.independent_bias=float={2} '
                 '{0}.reduction.non_minimal_weight_func=string=regular '
                 '{0}.reduction.max_outputs=uint=1 '
                 .format(loc, cbias, ibias))
    return cmd
  sw.add_variable('Congestion Bias', 'CB', congestion_bias,
                  set_congestion_bias)

  arbiters = {'AGE': 'comparing'} #, 'RR': 'lslp'}
  def set_arbiter(arb, config):
    return ('network.router.vc_scheduler.allocator.resource_arbiter.type='
            'string={0} '
            'network.router.vc_scheduler.allocator.client_arbiter.type='
            'string={0} '
            'network.router.crossbar_scheduler.allocator.resource_arbiter.type='
            'string={0} '
            'network.router.output_crossbar_scheduler='
            'ref=network.router.crossbar_scheduler '
            'network.interface.crossbar_scheduler='
            'ref=network.router.crossbar_scheduler '
            .format(arbiters[arb]))
  sw.add_variable('Arbitration', 'ARB', arbiters,
                  set_arbiter)

  def set_load(load, config):
    return ('workload.applications[0].blast_terminal.request_injection_rate='
            'float={0} '.format(0.001 if load == '0.00' else load))
  sw.add_loads('Load', 'LD', args.start, args.stop, args.step, set_load)

  ##############################################################################
  # analyses
  if not args.skip_analyses:
    sw.add_plot('time-latency-scatter', 'all', title_format='short-equal')
    sw.add_plot('latency-pdf', 'all', title_format='short-equal')
    sw.add_plot('latency-cdf', 'all', title_format='short-equal')
    sw.add_plot('latency-percentile', 'all', title_format='short-equal')
    sw.add_plot('load-latency', 'all', title_format='off',
                plot_style='inferno-markers', ymin='0',
                xmax=100) #, ymax='3000')
    sw.add_plot('load-latency-compare', 'all', title_format='off',
                plot_style='inferno-markers')
                #figure_size='10x4',
                #ymin=0, ymax=3000,
                #xmin=0, xmax=100,
                #legend_location=2)
    sw.add_plot('load-average-hops', 'all', title_format='off',
                yauto_frame=0.02)
    sw.add_plot('load-percent-minimal', 'all', title_format='short-equal',
                yauto_frame=0.02)

  ##############################################################################
  # run
  sw.create_tasks(tm)
  tm.run_tasks()


if __name__ == '__main__':
  ap = argparse.ArgumentParser()
  ap.add_argument('directory', help='run directory')
  ap.add_argument('start', type=int,
                  help='starting injection rate')
  ap.add_argument('stop', type=int,
                  help='stopping injection rate')
  ap.add_argument('step', type=int,
                  help='injection rate step')
  ap.add_argument('-l', '--log', type=argparse.FileType('w'), default=None,
                  help='output file for logging')
  ap.add_argument('-f', '--fail_fast', action='store_true',
                  help='quickly kill tasks upon any failure')
  ap.add_argument('-s', '--skip_analyses', action='store_true',
                  help='don\'t run analyses')
  ap.add_argument('-m', '--memory', type=float,
                  default=MemoryResource.current_available_memory_gib() /
                  os.cpu_count(),
                  help='memory per simulation')
  main(ap.parse_args())
