import re

import numpy as np
import pandas as pd

from wgdi import base


class collinearity:
    def __init__(self, options, matrix):
        self.gap_penality = -1
        self.over_length = 100000
        self.mg1 = 25
        self.mg2 = 25
        self.over_gap = 5
        self.path_dict = {}
        self.mat = matrix
        for k, v in options:
            setattr(self, str(k), v)
        if hasattr(self, 'mg'):
            self.mg1, self.mg2 = [int(k) for k in self.mg.split(',')]
        else:
            self.mg1, self.mg2 = [25, 25]

    def get_martix(self):
        self.mat.columns = self.mat.columns.astype(int)
        self.mat.index = self.mat.index.astype(int)
        (m, n) = self.mat.shape
        self.score1 = self.mat.copy()
        self.score2 = self.mat.copy()
        self.mat_new = self.mat.copy()
        self.matold = self.mat.copy()
        self.path1 = pd.DataFrame([['' for i in range(n)] for j in range(
            m)], index=self.mat.index, columns=self.mat.columns)
        self.path2 = pd.DataFrame([['' for i in range(n)] for j in range(
            m)], index=self.mat.index, columns=self.mat.columns)

    def run(self):
        self.get_martix()
        loc, evalues, scores = [], [], []
        while(self.over_length >= 3):
            if self.maxPath():
                loc.append(self.path)
                evalues.append(self.evalue)
                scores.append(self.score)
        return loc, evalues, scores

    def maxPath(self):
        mat_new_index, mat_new_columns = self.mat_new.index, self.mat_new.columns
        for i, row in enumerate(mat_new_index):
            for j, col in enumerate(mat_new_columns):
                if self.mat_new.loc[row, col] == 0:
                    continue
                for row_i in mat_new_index[i+1:i+1+self.mg1]:
                    if row_i - row > self.mg1:
                        break
                    for col_j in mat_new_columns[j+1:j+1+self.mg2]:
                        if col_j - col > self.mg2:
                            break
                        if self.mat_new.loc[row_i, col_j] == 0:
                            continue
                        s = self.score1.loc[row, col]+self.mat_new.loc[row_i,
                                                                       col_j]+(row_i-row-1+col_j-col-1)*self.gap_penality
                        if self.score1.loc[row_i, col_j] < s:
                            self.score1.loc[row_i, col_j] = s
                            self.path1.loc[row_i,
                                           col_j] = self.path1.loc[row, col]
                            self.path1.loc[row_i,
                                           col_j] += str(row)+':'+str(col)+'_'
        mat_new_index = mat_new_index[::-1]
        for i, row in enumerate(mat_new_index):
            for j, col in enumerate(mat_new_columns):
                if self.mat_new.loc[row, col] == 0:
                    continue
                for row_i in mat_new_index[i+1:i+1+self.mg1]:
                    if row - row_i > self.mg1 or row_i >= row:
                        break
                    for col_j in mat_new_columns[j+1:j+1+self.mg2]:
                        if col_j - col > self.mg2:
                            break
                        if self.mat_new.loc[row_i, col_j] == 0:
                            continue
                        s = self.score2.loc[row, col]+self.mat_new.loc[row_i,
                                                                       col_j]+(row-row_i-1+col_j-col-1)*self.gap_penality
                        if self.score2.loc[row_i, col_j] < s:
                            self.score2.loc[row_i, col_j] = s
                            self.path2.loc[row_i,
                                           col_j] = self.path2.loc[row, col]
                            self.path2.loc[row_i,
                                           col_j] += str(row)+':'+str(col)+'_'

        if self.score1.empty or self.score2.empty or self.score1.stack().max() == self.score2.stack().max() == 0:
            self.over_length = 0
            self.path = []
            self.evalue = np.nan
            self.score = 0
            return False
        if self.score1.stack().max() >= self.score2.stack().max():
            (x, y) = self.score1.stack().idxmax()
            self.score = self.score1.loc[x, y]
            self.path1.loc[x, y] += str(int(x))+':'+str(y)+'_'
            array = re.findall('\d+', self.path1.loc[x, y])
            self.path = [[int(array[i]), int(array[i+1])]
                         for i in range(0, len(array), 2)]
        else:
            (x, y) = self.score2.stack().idxmax()
            self.score = self.score2.loc[x, y]
            self.path2.loc[x, y] += str(int(x))+':'+str(y)+'_'
            array = re.findall('\d+', self.path2.loc[x, y])
            self.path = [[int(array[i]), int(array[i+1])]
                         for i in range(0, len(array), 2)]
        self.over_length = len(self.path)
        (x1, y1), (x2, y2) = self.path[0], self.path[-1]
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        x_gap, y_gap = [], []
        for k in self.mat.index:
            if k <= x2+self.mg1 and k >= x1 - self.mg1:
                x_gap.append(k)
        for k in self.mat.columns:
            if k <= y2 + self.mg2 and k >= y1-self.mg2:
                y_gap.append(k)
        del_x = [k for k in self.mat.index if x1 <= k <= x2]
        del_y = [k for k in self.mat.columns if y1 <= k <= y2]
        mark = False
        if self.right_path():
            for row, col in self.path:
                self.mat.loc[row, col] = 0
        else:
            mark = True
        self.score1.loc[x_gap, y_gap] = 0
        self.score2.loc[x_gap, y_gap] = 0
        self.path1.loc[x_gap, y_gap] = ''
        self.path2.loc[x_gap, y_gap] = ''
        self.mat_new = self.mat.loc[x_gap, y_gap]
        self.mat_new = self.mat_new.loc[:, self.mat_new.sum(axis=0) != 0]
        self.mat_new = self.mat_new.loc[self.mat_new.sum(axis=1) != 0, :]
        if mark:
            return False
        self.evalue = self.evalue_estimated()
        return True

    def right_path(self):
        for k in self.path:
            if str(k[0])+':'+str(k[1]) in self.path_dict:
                return False
        for k in self.path:
            self.path_dict[str(k[0])+':'+str(k[1])] = 1
        return True

    def evalue_estimated(self):
        (x1, y1), (x2, y2) = self.path[0], self.path[-1]
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        N = 0
        for (x, y) in self.path:
            mat = self.matold.loc[x, self.matold.columns.isin(
                range(y-int(self.mg2*0.5), y+int(self.mg2*0.5)))]
            mat[mat > 0] = 1
            N += mat.sum()
        m = len(self.path)
        L1, L2 = x2-x1+1, y2-y1+1
        a = (N-m+1)/N*(L1-m+1)*(L2-m+1)/L1/L2/m
        return round(a, 4)
