#include <math.h>
#include <stdlib.h>
#include <queue>

#include "mex.h"
#include "graph.h"


void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]){
 	
	if (nrhs != 2)
		mexErrMsgTxt("2 input arguments are required");
	if (nlhs != 4)
		mexErrMsgTxt("Number of outputs is not correct - should be 4");

	////////// Check dimension of the input data /////////////////////////////

	const int *sizeDimUnary = mxGetDimensions(prhs[0]);
	const int *sizeDimEdge = mxGetDimensions(prhs[1]);

	
	int nrows = sizeDimUnary[0]; 
	int ncols = sizeDimUnary[1]; 
	int layers = sizeDimUnary[2];

	const int nodeNum = nrows*ncols; // number of nodes

	const int edgeNum = sizeDimEdge[1];

	if(sizeDimEdge[0] != 3)
		mexErrMsgTxt("Edge matrix should be 3*n_edges");

	double *UnaryPtr = mxGetPr(prhs[0]);
	double *edgePtr = mxGetPr(prhs[1]);

	/////////////////////// create graph //////////////////////
	typedef Graph<double,double,double> GraphType;
	GraphType *g = new GraphType(nodeNum,edgeNum); 
	g -> add_node(nodeNum);

	///////////// Add data term ////////////////////////////
	if(layers !=2){
		for (int i = 0; i < nodeNum; i++){
			g -> add_tweights(i,UnaryPtr[i],0);
		}
	}
	else{
		for (int i = 0; i < nodeNum; i++){
			g -> add_tweights(i,UnaryPtr[nodeNum + i],UnaryPtr[i]);
		}
	}
		
	///////////// Add edge term ////////////////////////////
	for (int i = 0; i < edgeNum; i++){
		g -> add_edge((int) edgePtr[i*3], (int) edgePtr[i*3+1], edgePtr[i*3+2],edgePtr[i*3+2]);
	}

	double MAP_energy = g -> maxflow();

                   
	//////////////////////////////// ASSIGN OUTPUT //////////////////////////
	plhs[0] = mxCreateDoubleMatrix(nrows, ncols,  mxREAL);
	double *labelOutPtr = mxGetPr(plhs[0]); 

	for (int j=0; j<nodeNum; j++)
	{
		labelOutPtr[j] = (double) g->what_segment(j);
	}

	plhs[1] = mxCreateDoubleMatrix(1, 1,  mxREAL);
	double *energyPtr = mxGetPr(plhs[1]); 
	energyPtr[0] = MAP_energy;


	//////////////////////////////// COMPUTE MIN-MARGINALS //////////////////////////
	plhs[2] = mxCreateDoubleMatrix(nrows, ncols,  mxREAL);
	double *minMarginal0Ptr = mxGetPr(plhs[2]); 

	plhs[3] = mxCreateDoubleMatrix(nrows, ncols,  mxREAL);
	double *minMarginal1Ptr = mxGetPr(plhs[3]); 

	double hard_constraint = ((((unsigned)-1)/2));
	for (int j=0; j<nodeNum; j++)
	{
		if (labelOutPtr[j] == 1)
		{
			g -> mark_node(j);
			g -> add_tweights(j,hard_constraint,0);
			
			minMarginal0Ptr[j] = g -> maxflow(1);
			minMarginal1Ptr[j] = MAP_energy; 
			
			g -> add_tweights(j,-hard_constraint,0);
			g -> mark_node(j);
		}
		else
		{
			g -> mark_node(j);
			g -> add_tweights(j,0,hard_constraint);
			
			minMarginal1Ptr[j] = g -> maxflow(1);
			minMarginal0Ptr[j] = MAP_energy; 
			
			g -> mark_node(j);
			g -> add_tweights(j,0, -hard_constraint);
		}
	}

	delete g;


}


