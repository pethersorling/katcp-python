import math
import json

class Result(object):
    def __init__(self, scenario, interpreter, lib, result):
        self.scenario = scenario
        self.interpreter = interpreter
        self.lib = lib
        self.result = result

results = [Result('scenario1', 'cpython 2.6.5', 'katcp',
                  [(2875, 1), (2741, 1), (2591, 1), (2730, 1), (2808, 1), (2547, 1), (1077, 2), (1013, 2), (1218, 2), (1017, 2), (1228, 2), (1127, 2), (1151, 3), (1039, 3), (1196, 3), (1603, 3), (951, 3), (1207, 3), (1069, 4), (1086, 4), (1001, 4), (1291, 4), (1188, 4), (1096, 4), (1028, 5), (879, 5), (894, 5), (879, 5), (810, 5), (999, 5)]),
           Result('scenario1', 'cpython 2.6.5', 'txkatcp',
                  [(2246, 1), (2640, 1), (2292, 1), (2238, 1), (2285, 1), (2274, 1), (2173, 2), (1860, 2), (2217, 2), (2308, 2), (2234, 2), (2322, 2), (1983, 3), (2007, 3), (2010, 3), (1989, 3), (2023, 3), (2081, 3), (1952, 4), (1951, 4), (1796, 4), (1811, 4), (1959, 4), (1851, 4), (1780, 5), (1895, 5), (1821, 5), (1822, 5), (1715, 5), (1775, 5)]),
           Result('scenario1', 'pypy-c-78182-jit32', 'katcp',
                  [(3658, 1), (3658, 1), (3657, 1), (3536, 1), (3659, 1), (3658, 1), (5426, 2), (4855, 2), (4620, 2), (5422, 2), (4503, 2), (4886, 2), (1768, 3), (1506, 3), (1636, 3), (1627, 3), (1360, 3), (1856, 3), (1545, 4), (1716, 4), (1279, 4), (1512, 4), (1849, 4), (1673, 4), (1328, 5), (1552, 5), (1851, 5), (1766, 5), (1336, 5), (1493, 5)]),
           Result('scenario1', 'pypy-c-78182-jit32', 'txkatcp',
                  [(2443, 1), (2444, 1), (2447, 1), (2440, 1), (2439, 1), (2438, 1), (4994, 2), (4860, 2), (3626, 2), (3808, 2), (3780, 2), (3580, 2), (3704, 3), (3477, 3), (3805, 3), (3693, 3), (3784, 3), (3740, 3), (3234, 4), (3143, 4), (3223, 4), (2942, 4), (3223, 4), (3203, 4), (2146, 5), (2338, 5), (2645, 5), (2523, 5), (2600, 5), (2193, 5)]),
           Result('scenario2', 'cpython 2.6.5', 'katcp', [(650.45161290322585, 1), (637.32258064516134, 1), (649.22580645161293, 1), (642.41935483870964, 1), (651.25806451612902, 1), (646.48387096774195, 1), (646.58064516129036, 2), (665.9354838709678, 2), (666.38709677419365, 2), (654.9354838709678, 2), (660.16129032258073, 2), (652.32258064516134, 2), (660.16129032258061, 3), (664.58064516129025, 3), (664.18709677419349, 3), (636.45161290322585, 3), (648.22580645161293, 3), (654.51612903225805, 3), (642.12903225806463, 4), (669.0, 4), (654.74193548387098, 4), (655.25806451612902, 4), (657.67741935483866, 4), (661.54838709677415, 4), (655.87096774193549, 5), (671.74193548387098, 5), (671.48387096774184, 5), (640.77419354838707, 5), (636.45161290322585, 5), (650.64516129032256, 5)]),
           Result('scenario2', 'cpython 2.6.5', 'txkatcp', [(548.83870967741939, 1), (550.51612903225805, 1), (554.58064516129036, 1), (531.83870967741939, 1), (545.16129032258061, 1), (534.12903225806451, 1), (578.09354838709669, 2), (560.87849462365591, 2), (563.23118279569894, 2), (554.51397849462364, 2), (538.12903225806451, 2), (567.16129032258073, 2), (602.44623655913983, 3), (586.25806451612902, 3), (589.90215053763438, 3), (580.0, 3), (601.50967741935483, 3), (594.58064516129036, 3), (594.9064516129032, 4), (607.9354838709678, 4), (590.93548387096769, 4), (595.72473118279572, 4), (581.34086021505368, 4), (600.50537634408602, 4), (578.9354838709678, 5), (541.32258064516122, 5), (557.22580645161293, 5), (576.09677419354841, 5), (599.40322580645159, 5), (603.18172043010759, 5)]),
           Result('scenario2', 'pypy-c-78182-jit32', 'katcp', [(867.48387096774195, 1), (888.16129032258061, 1), (902.74193548387098, 1), (866.74193548387098, 1), (870.83870967741939, 1), (892.0322580645161, 1), (837.38709677419354, 2), (891.0322580645161, 2), (861.9677419354839, 2), (871.0967741935483, 2), (883.61290322580646, 2), (899.09677419354841, 2), (880.8709677419356, 3), (873.64516129032268, 3), (888.58064516129025, 3), (846.12903225806463, 3), (809.9354838709678, 3), (837.90322580645159, 3), (843.54838709677415, 4), (816.0, 4), (849.54838709677415, 4), (870.1612903225805, 4), (836.25806451612902, 4), (869.90322580645159, 4), (533.16129032258061, 5), (552.64516129032256, 5), (566.74193548387098, 5), (848.48387096774195, 5), (607.74193548387098, 5), (538.77419354838707, 5)]),
           Result('scenario2', 'pypy-c-78182-jit32', 'txkatcp',[(762.70967741935488, 1), (751.0, 1), (750.19354838709683, 1), (759.64516129032256, 1), (747.9677419354839, 1), (756.09677419354841, 1), (736.54838709677415, 2), (721.51612903225805, 2), (675.0967741935483, 2), (775.51612903225805, 2), (797.0, 2), (782.61290322580646, 2), (792.64516129032245, 3), (557.22580645161293, 3), (785.41935483870975, 3), (806.64516129032245, 3), (786.51612903225805, 3), (775.51612903225805, 3), (537.16129032258073, 4), (536.80645161290317, 4), (538.87096774193549, 4), (533.58064516129025, 4), (536.9354838709678, 4), (517.74193548387098, 4), (516.32258064516134, 5), (555.67741935483866, 5), (732.32258064516122, 5), (515.77419354838707, 5), (520.48387096774195, 5), (513.64516129032256, 5)]
               )
           ]

def compute_all(all):
    colors = ['green', 'red', 'yellow', 'brown']

    retval = {}
    
    for ii, result in enumerate(all):
        d = {}
        max_clients = max([i for v, i in result.result])
        res = [None] * max_clients
        errors = [None] * max_clients
        for no, clients in result.result:
            d.setdefault(clients, []).append(no)
        for clients, v in d.items():
            s = sum(v)/len(v)
            df = math.sqrt(sum([(s - i)*(s - i) for i in v]) / (len(v) - 1))
            res[clients - 1] = s
            errors[clients - 1] = df
        retval.setdefault(result.scenario, []).append({
            'result' : res,
            'lib': result.lib,
            'interpreter' : result.interpreter,
            'errors': errors})
    return retval

if __name__ == '__main__':
    with open('out.json', 'w') as f:
        json.dump(compute_all(results), f)
