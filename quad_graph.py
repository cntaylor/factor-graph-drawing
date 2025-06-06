import numpy as np
import scipy.sparse as sp
import random
import os

def write_LaTeX_graph_preamble(f):
    '''
    Assume an already open file (f).  Write to it
    
    Inputs:
        f: open file object
    
    Outputs:
        None
    '''
    f.write(r'\documentclass[convert]{standalone}' + '\n') #[convert] means it generates a .png :)
    f.write(r'\usepackage{tikz}' + '\n')
    f.write(r'\usetikzlibrary{positioning, shapes.arrows, arrows.meta, calc}' + '\n')
    f.write(r'\definecolor{blue}{RGB}{0,128,255}' + '\n')
    f.write(r'\definecolor{green}{RGB}{15,180,0}' + '\n')
    f.write(r'\definecolor{yellow}{RGB}{255,226,0}' + '\n')
    f.write(r'\tikzstyle{hidden}=[circle, minimum size = .9cm, draw=black, thick]' + '\n')
    f.write(r'\tikzstyle{factor}=[rectangle, draw=black,fill=black,text=white]' + '\n')
    f.write(r'\tikzstyle{dyn}=[rectangle, draw=green,fill=green]' + '\n')
    f.write(r'\tikzstyle{betweenfactor}=[rectangle, draw=red,fill=red]' + '\n')
    f.write(r'% Things for drawing the matrices nicely (to correspond with colors in the graph)' + '\n')
    f.write(r'\newcommand{\greenbox}{\textcolor{green}{\rule{4pt}{4pt}}}' + '\n')
    f.write(r'\newcommand{\blackbox}{\rule{4pt}{4pt}}' + '\n')

def LaTeX_graph_from_sp_matrix(A, filename):
    # This function assumes the A matrix is divided into two parts:
    # Unary factors and Non-unary factors.
    # The non-unary factors can be either "dynamics" or "between factors"
    # It assumes dynamics are defining a node before it is used by a between factor
    # No error checking ... just assumes all non-unary things are either dynamics or between factors
    # Uses dynamics to create all nodes first (will search for non-unary part, process that first, then unary)

    assert isinstance(A, sp.csr_matrix), "Input must be a sparse matrix of type csr_matrix"

    def is_factor(i):
        return (A[i,:].nnz == 1)

    # First, check if the file exists.  If not, go for it.
    if filename[-4:] != '.tex':
        filename = filename + '.tex'
    if os.path.isfile(filename):
        print('File exists.  Overwrite? (y/n) ', end='')
        response = input()
        if not response.lower().startswith('y'):
            print('Exiting without overwriting file.')
            return
    f = open(filename, 'w')
    
    write_LaTeX_graph_preamble(f)
    f.write(r'\begin{document}' + '\n')
    f.write(r'\begin{tikzpicture}[scale=1.0]' + '\n')
    f.write(r'\node[hidden] (x0) {$x_0$};' + '\n')
    curr_row=0
    curr_hv = 0
    curr_bf = 0
    passed_factors=False
    # Make sure the dynamics comes first
    while is_factor(curr_row):
        passed_factors=True
        curr_row+=1
    while curr_row < A.shape[0] and not is_factor(curr_row):
        # Check if a dynamics or between factor
        # Get the non-zero entries for this row
        tst_list = A.indices[A.indptr[curr_row]:A.indptr[curr_row+1]].tolist()
        if tst_list[0] == tst_list[1]-1: # Dynamics
            f.write(f'\\node[dyn, right of = x{curr_hv}] (d{curr_hv}) {{}};' + '\n')
            f.write(f'\\node[hidden, right of = d{curr_hv}] (x{curr_hv+1}) {{$x_{{{curr_hv+1}}}$}};' + '\n')
            f.write(f'\\draw (x{curr_hv}) to (d{curr_hv});' + '\n')
            f.write(f'\\draw (d{curr_hv}) to (x{curr_hv+1});' + '\n')
            curr_hv+=1
        else: # Between factor
            f.write(f'\\coordinate (bm{curr_bf}) at ($(x{tst_list[0]})!.5!(x{tst_list[-1]})$) ;' + '\n')
            f.write(f'\\node[betweenfactor, above of = bm{curr_bf}, node distance = 1cm] (bf{curr_bf}) {{}};' + '\n')
            for x_node in tst_list:
                f.write(f'\\draw (x{x_node}) to (bf{curr_bf});' + '\n')
            curr_bf+=1
        curr_row+=1 
    if passed_factors:
        curr_row=0
    while curr_row < A.shape[0] and is_factor(curr_row):
        # First, determine how many measurements there are associated
        # with the same state
        hv_idx = A.indices[A.indptr[curr_row]]
        check_next_row = curr_row < A.shape[0] - 1
        # Only handle 0, 1, or 2 measurements! ... I already know it's not 0
        if check_next_row and A.indices[A.indptr[curr_row+1]] == hv_idx:
            # f.write(f'\\node[factor, below left of = x{hv_idx}, node distance = 1cm] (m{curr_row}) {{$m_{{{hv_idx},{0}}}$}};' + '\n')
            # f.write(f'\\node[factor, below right of = x{hv_idx}, node distance = 1cm] (m{curr_row+1}) {{$m_{{{hv_idx},{1}}}$}};' + '\n')
            f.write(f'\\node[factor, below of = x{hv_idx}, node distance = .8cm] (m{curr_row}) {{}};' + '\n')
            f.write(f'\\node[factor, below right of = x{hv_idx}, node distance = .8cm] (m{curr_row+1}) {{}};' + '\n')
            f.write(f'\\draw (x{hv_idx}) to (m{curr_row});' + '\n')
            f.write(f'\\draw (x{hv_idx}) to (m{curr_row+1});' + '\n')
            curr_row+=2
        else:
            # f.write(f'\\node[factor, below of = x{hv_idx}, node distance = .8cm] (m{curr_row}) {{$m_{{{hv_idx},{0}}}$}};' + '\n')
            f.write(f'\\node[factor, below of = x{hv_idx}, node distance = .8cm] (m{curr_row}) {{}};' + '\n')
            f.write(f'\\draw (x{hv_idx}) to (m{curr_row});' + '\n')
            curr_row+=1



    f.write(r'\end{tikzpicture}' + '\n')
    f.write(r'\end{document}' + '\n')
    f.close()


if __name__ == '__main__':
    graph_filename = 'quad_graph'
    A = sp.csr_matrix(np.array([[1,0,0,0,0],
                                [0,1,0,0,0],
                                [0,1,0,0,0],
                                [0,0,1,0,0],
                                [0,0,0,1,0],
                                [0,0,0,1,0],
                                [0,0,0,0,1],
                                [1,1,0,0,0],
                                [0,1,1,0,0],
                                [0,0,1,1,0],
                                [0,0,0,1,1],
                                [1,0,0,1,1]
                                ]))
    LaTeX_graph_from_sp_matrix(A, graph_filename)
    os.system('pdflatex '+graph_filename+'.tex -output-directory=./')
    # Use this next command if you want to convert to a .png.
    # density makes it the same size (and look good), alpha and background makes it a white background, no transparent
    os.system('magick -density 300 '+graph_filename+'.pdf -background white -alpha off '+graph_filename+'.png')
    for f in os.listdir('.'):
        if f.endswith('.log') or f.endswith('.aux'):
            os.remove(f)

    exit()

