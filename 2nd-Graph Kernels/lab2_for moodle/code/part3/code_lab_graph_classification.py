#!/usr/bin/env python


"""
Graph Mining and Analysis with Python - Master Data Science - MVA - Feb 2017

Graph Classification
"""

import networkx as nx
import numpy as np
from scipy.sparse.linalg import eigs
from random import randint
import time
from sklearn import cluster
from community_detection import louvain
from kernel_eval import svm_classification
from baseline_kernels import (compute_graphlet_kernel,compute_wl_subtree_kernel)


# Load the graph into an undirected NetworkX graph

##################
# your code here #
##################

# hint: use read_edgelist function of NetworkX
G = nx.read_edgelist("../dataset/CA-HepTh.txt", comments='#', delimiter='\t', nodetype=int, create_using=nx.Graph())


# Get giant connected component (GCC)

##################
# your code here #
##################

# hint: use connected_component_subgraphs function of NetworkX, GCC is the biggest of the subgraphs
GCC = max(nx.connected_component_subgraphs(G), key=len)



# Spectral clustering algorithm
# Implement and apply spectral clustering

def spectral_clustering(G, k):
    L = nx.normalized_laplacian_matrix(G).astype(float) # Normalized Laplacian

    # Calculate k smallest in magnitude eigenvalues and corresponding eigenvectors of L

    ##################
    # your code here #
    ##################
    
    # hint: use eigs function of scipy
    eigval, eigvec = eigs(L, k=k, which='SR')

    eigval = eigval.real # Keep the real part
    eigvec = eigvec.real # Keep the real part
    # sort is implemented by default in increasing order
    idx = eigval.argsort() # Get indices of sorted eigenvalues
    eigvec = eigvec[:,idx] # Sort eigenvectors according to eigenvalues
    
    # Perform k-means clustering (store in variable "membership" the clusters to which points belong)
    
    ##################
    # your code here #
    ##################
    
    # hint: use KMeans class of scikit-learn
    km = cluster.KMeans(n_clusters=k, init='random').fit(eigvec)


    membership = list(km.labels_)
    # will contain node IDs as keys and membership as values
    clustering = {}
    nodes = G.nodes()
    for i in range(len(nodes)):
        clustering[nodes[i]] = membership[i]
    
    return clustering




def create_dataset(GCC):
	# Apply spectral clustering to the CA-HepTh dataset
	clustering_spectral = spectral_clustering(GCC, 60)

	# Apply louvain to the CA-HepTh dataset
	clustering_louvain = louvain(GCC)
	
	graphs = []
	labels = []
	
	clusters = {}
	for node in clustering_spectral:
		if clustering_spectral[node] in clusters:
			clusters[clustering_spectral[node]].append(node)
		else:
			clusters[clustering_spectral[node]] = [node]

	for cluster in clusters:
		graphs.append(GCC.subgraph(clusters[cluster]))
		labels.append(-1)
	
		
	clusters = {}
	for node in clustering_louvain:
		if clustering_louvain[node] in clusters:
			clusters[clustering_louvain[node]].append(node)
		else:
			clusters[clustering_louvain[node]] = [node]

	for cluster in clusters:
		graphs.append(GCC.subgraph(clusters[cluster]))
		labels.append(1)

	return graphs,labels

	
graphs,labels = create_dataset(GCC)


# Embed the nodes of all graphs in the d-dimensional
# space using the eigenvectors of the d largest in
# magnitude eigenvalues

def compute_node_embeddings(graphs, d):
	Us = []
	for G in graphs:
		n = G.number_of_nodes()
		A = nx.adjacency_matrix(G).astype(float)
		

		# Perform eigenvalue decomposition of the adjacency matrix and keep the d largest in magnitude eigenvalues (Store into variable U)
    
	    ##################
	    # your code here #
	    ##################

	    # hint: use eigs function of scipy
		if n > d+1:
			Lambda, U = eigs(A, k=d)
			idx = Lambda.argsort()[::-1]
			U = U[:, idx]
		else:
			Lambda, U = np.linalg.eig(A.todense())
			idx = Lambda.argsort()[::-1]
			U = U[:, idx]
			U = U[:,:d]


		U = np.absolute(U);
		Us.append(U)
		
	return Us
	


# Pyramid match graph kernel
# Implement and compute it (L=5, d=10)

def compute_pm_kernel(graphs, L, d):
	start_time = time.time()
	
	N = len(graphs)
	
	Us = compute_node_embeddings(graphs, d)
		
	Hs = {}
	for i in range(N):
		Hs[i] = []
		for j in range(L):
		    l = 2**j
		    D = np.zeros((d, l))
		    T = np.floor(Us[i]*l)
		    T[np.where(T==l)] = l-1
		    for p in range(Us[i].shape[0]):
		        for q in range(Us[i].shape[1]):
		            D[q,int(T[p,q])] = D[q,int(T[p,q])] + 1
		            
		    Hs[i].append(D)
		    
		    
	K = np.zeros((N,N))
    
	for i in range(N):
		for j in range(i,N):
			k = 0
			intersec = np.zeros(L)
			for p in range(L):
			    intersec[p] = np.sum(np.minimum(Hs[i][p], Hs[j][p]))
			
			
			# Compute Kij kernel value for graphs i,j using equation 3
    
		    ##################
		    # your code here #
		    ##################
			k = k + intersec[L-1]
			for p in range(L-1):
				k = k + (1.0/(2**(L-p-1)))*(intersec[p]-intersec[p+1])

			K[i, j] = k
			K[j, i] = K[i, j]
		    
	
	end_time = time.time()
	print "Total time for Pyramid Match kernel: ", (end_time - start_time)

	return K


K = compute_pm_kernel(graphs, 5, 10)



# Evaluate the performance of the pyramid match kernel
# Print average accuracy

result = svm_classification(K,labels)
print "Accuracy Pyramid Match: ", result["mean_accuracy"]
print



# Graphlet kernel and WL subtree kernel
# Compute the kernel matrices and evaluate the
# two kernels

K = compute_graphlet_kernel(graphs)
result = svm_classification(K,labels)
print "Accuracy Graphlet: ", result["mean_accuracy"]
print

K = compute_wl_subtree_kernel(graphs,6)
result = svm_classification(K,labels)
print "Accuracy WL: ", result["mean_accuracy"]

""""
Print result,

Total time for Pyramid Match kernel:  2.23870897293
Accuracy Pyramid Match:  0.765909090909

Total time for Graphlet kernel:  1.40201497078
Accuracy Graphlet:  0.651515151515

Number of compressed labels at iteration 0: 6507
Number of compressed labels at iteration 1: 10981
Number of compressed labels at iteration 2: 11715
Number of compressed labels at iteration 3: 11816
Number of compressed labels at iteration 4: 11837
Number of compressed labels at iteration 5: 11840
Total time for WL subtree kernel:  3.36044096947
Accuracy WL:  0.782575757576

""""