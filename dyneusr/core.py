"""
DyNeuGraph class definition
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import json

import numpy as np 
import pandas as pd
import networkx as nx

from sklearn.base import BaseEstimator, TransformerMixin

from dyneusr import datasets
from dyneusr import visuals
from dyneusr import tools



class DyNeuGraph(BaseEstimator, TransformerMixin):

    def __init__(self, **params):
        """ DyNeuGraph
        
        Parameters
        ----------

        Usage
        -----

            # Fit DyNeuGraph
            dyneuG = dy.DyNeuGraph()
            dyneuG.fit(X)

            # Transform Mapper graph
            tcm = dyneuG.transform(graph)       # [T x N] Time-Node adjacency
    
            # Annotate
            dyneuG.annotate(microstates=dict(color='blue'))

            # Visualize
            dyneuG.visualize()
        """
        self.cache_ = dict(params)
        self.fit(**params)


    def cache(self, *args, **kwargs):
        """ Cache misc. data here

        TODO: hacky, replace with getter/setter
        """
        # return value, if arg is passed
        if len(args):
            for _ in args:
                if self.cache_.get(_) is None:
                    continue
                return self.cache_.get(_)
            return None
        # otherwise, update
        self.cache_.update(kwargs)
        return self.cache_



    def fit(self, G=None, X=None, y=None, node_data=dict(), edge_data=dict(), G_data=False, **kwargs):
        """ Fit to G.

        Usage
        -----
            # Transform Mapper graph
            dyneuG.fit(graph, y=meta)       

        """
        # save inputs
        self.G_input_ = G
        self.X_ = X 
        self.y_ = y

        # check graph
        if isinstance(G, nx.Graph):
            g = G.copy()
            G = nx.node_link_data(g)
        elif G is None:
            G = {}

        # copy graph, override defaults
        G = dict(dict(nodes={}, links={}), **G)

        # states, microstates
        node_ids = np.unique([n for i,n in enumerate(G['nodes'])])
        data_ids = np.unique([_ for n,d in G['nodes'].items() for _ in d])
        if y is not None:
            if isinstance(y, pd.DataFrame):
                data_ids = np.sort(y.reset_index().index)
            else:
                data_ids = np.arange(len(y))

        # process graph
        G = tools.process_graph(G, meta=y, **kwargs)
        A, M, TCM = tools.extract_matrices(G, index=data_ids)

        # create graph from TCM
        if G_data is True:
            G_data = nx.MultiGraph(TCM)
            nx.relabel_nodes(G_data, dict(zip(G_data, data_ids)))
            nx.set_node_attributes(G_data, dict(zip(data_ids, y)), 'group')

        # annotate any additional node datahere
        if node_data is not None:
            for k in node_data:
                nx.set_node_attributes(G, dict(node_data[k]), k)
        if edge_data is not None:
            for k in edge_data:
                   nx.set_edge_attributes(G, dict(edge_data[k]), k)

        # mixture of connected TRs, for each TR 
        mixtures = [_.nonzero()[0] for _ in TCM]


        # store variables
        self.G_ = G
        self.G_data_ = G_data
        self.node_ids_ = node_ids 
        self.data_ids_ = data_ids
        self.adj_ = A               # node adjacency matrix
        self.map_ = M             # node attr matrix
        self.tcm_ =  TCM                # temporal connectivity
        self.mixtures_ = mixtures

        # some new conventions
        self.G = self.G_
        self.A = self.adj_
        self.M = self.map_
        self.TCM = self.tcm_
        return self


    def inverse_transform(self, G, y=None):
        """ Inverse transform of G 
        """
        return self.G_inverse_


    def fit_transform(self, G, y=None):
        """ Transform Mapper graph into populations.

        Usage
        -----
            # Transform Mapper graph
            assigns = dyneuG.fit_transform(graph, y=meta)      

        """
        # fit
        self.fit(G=G, y=y)
        return self.tcm_


    def sample(self, X, y=None):
        """ Predict Mixture Models using data based on TCM
        """
        mixtures_img = None
        # TODO:
        self.mixtures_img_ = mixtures_img
        return self.mixtures_img_    


    def transform(self, X, y=None):
        """ Transform X into TCM.

        Usage
        -----
            # Transform Mapper graph
            TCM = dyneuG.transform(X, y=meta)      

        """
        A, M, TCM = tools.extract_matrices(self.G_)

        # create graph from TCM
        if G_data is True:
            G_data = nx.MultiGraph(TCM)
            nx.relabel_nodes(G_data, dict(zip(G_data, data_ids)))
            nx.set_node_attributes(G_data, dict(zip(data_ids, y)), 'group')


        # mixture of connected TRs, for each TR 
        mixtures = [_.nonzero()[0] for _ in TCM]

        # store variables
        self.G_data_ = G_data
        self.adj_ = A               # node adjacency matrix
        self.map_ = M             # node attr matrix
        self.tcm_ =  TCM                # temporal connectivity
        self.mixtures_ = mixtures
        return self.tcm_


    def annotate(self, **kwargs):
        """ Annotate graph with data.

        TODO: not sure how to do this...
        """
        G_, annotations = visuals.annotate(self.G_, **kwargs)
        
        # save
        self.G_ = G_
        self.annotations_ = annotations
        return self


    def annotate_nodes(self, **kwargs):
        """    Set node attributes from dictionary of nodes and values. 

        Parameters
        ----------
            name: string
                Attribute name
            values: dict
                Dictionary of attribute values keyed by node.
            kwargs: dict
                Dictionary of attribute values keyed by name.
        
        Examples
        --------
            dG.annotate_nodes(color='blue')


        """
        for name, values in kwargs.items():
            if isinstance(values, np.ndarray):
                values = list(values)
            elif isinstance(values, dict):
                values = values.keys()
            elif not isinstance(values, list):
                values = [values for _ in self.G_]
            values = {n:value for n,value in zip(self.G_,values)}
            nx.set_node_attributes(self.G_, values, name)
        #nx.set_node_attributes(self.G_, name, values)
        
        # save
        return self


    def annotate_members(self, **kwargs):
        """    Set node attributes from dictionary of members and values. 

        Parameters
        ----------
            name: string
                Attribute name
            values: dict
                Dictionary of attribute values keyed by node.
            kwargs: dict
                Dictionary of attribute values keyed by name.

        Examples
        --------
            dG.annotate_node(image=data_imgs)

        """
        # TODO: map_from_nodes
        for name, values in kwargs.items():
            if isinstance(values, np.ndarray):
                values = list(values)
            elif isinstance(values, dict):
                values = values.keys()
            elif not isinstance(values, list):
                values = [values]
            # map attrs to data_ids
            values = {n:value for n,value in zip(self.G_data_,values)}
            nx.set_node_attributes(self.G_data_, values, name)

        # save
        return self


    def annotate_graph(self, **kwargs):
        """ Annotate graph with data.
        """
        self.G_.graph.update(**kwargs)
        return self


    def visualize(self, path_html='index.html', json_graph=None, color_functions=None, custom_data=None, plot_tcm=False, **kwargs):
        """ Visualize DyNeuGraph.

        TODO: this needs some work...
        """
        # color functions
        if color_functions is not None:
            if not isinstance(color_functions, dict):
                color_functions = dict(default=color_functions)
            self.G.graph.update(color = color_functions)

        

        # format html
        if isinstance(custom_data, dict):
            self.annotate_graph(**custom_data)
        
        # to node_link
        self.node_link_data_ = dict(nx.node_link_data(self.G))

        # [1] plot TCM
        if plot_tcm:
            figs = visuals.plot_temporal_matrix(self.tcm_, y=None, show=True, **kwargs)

        # [2] visualize force
        HTTP = visuals.visualize_force(self.node_link_data_, path_html=path_html, **kwargs)
        self.HTTP = HTTP
        return self


