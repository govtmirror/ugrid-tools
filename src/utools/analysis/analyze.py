from collections import OrderedDict
from csv import DictWriter

import matplotlib.pyplot as plt
import numpy as np

from utools.analysis.db import Session, VectorProcessingUnit, Catchment


def report(csv_path):
    s = Session()
    records = []
    for vpu in s.query(VectorProcessingUnit).order_by(VectorProcessingUnit.name):
        record = OrderedDict()
        record['Vector Processing Unit'] = vpu.name
        record['Elements'] = len(vpu.catchment)
        record['Nodes'] = vpu.get_node_count()
        record['Max Nodes in Element'] = vpu.get_max_node_count()
        record['Area (km^2)'] = vpu.get_area() * 1e-6
        if not vpu.name.startswith('13'):
            record['Create Weights (Minutes, 256 Cores)'] = vpu.timing[0].create_weights / 60
            record['Apply Weights (Seconds, 256 Cores)'] = vpu.timing[0].apply_weights_calculation
        else:
            record['Apply Weights (Seconds, 256 Cores)'] = None
            record['Create Weights (Minutes, 256 Cores)'] = None
        records.append(record)

    with open(csv_path, 'w') as f:
        writer = DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def boxplot_node_distribution():
    """Create boxplot of node distribution."""

    s = Session()
    nodes = np.array(s.query(Catchment.node_count).all()).squeeze()
    n, bins, patches = plt.hist(nodes, bins=10, cumulative=True)  # , normed=1)#, facecolor='green', alpha=0.75)
    # plt.boxplot(nodes, )
    plt.show()
    s.close()


if __name__ == '__main__':
    # report('/tmp/out.csv')
    # boxplot_node_distribution()
    # get_representative_nodes()
    pass
