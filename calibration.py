import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from collections import defaultdict



class Quantitation():

    def __init__(self):
        d= defaultdict(lambda: None)
        self.result_files = defaultdict(lambda: None)
        self.result_image = defaultdict(lambda: None)
        self.input_files= defaultdict(lambda: None)




    # ======== WORKSPACES ============

    def filepath(self, area, ppm):
        self.input_files['area']= area
        self.input_files['ppm']= ppm

    def savepath(self, path):
        self.input_files['savefile']= path


    def normalize_quantitation(self):
        df1= pd.read_excel(self.input_files['area'])
        df1.columns= [x.lower() for x in df1.columns]
        df1.columns= [re.sub(' ', '', x) for x in df1.columns]
        df1.columns= [x.strip('(keds)') for x in df1.columns]
        df1= df1.dropna(how = 'all')
        df1= df1.dropna(subset=['label'])
        df1['label']= df1['label'].astype(str)
        df1['label']= [x.lower() for x in df1['label']]
        df1['label']= [re.sub(' ', '', x) for x in df1['label']]
        df1['label']= [re.sub(r'\W+', '', x) for x in df1['label']]
        xx = [x for x in df1['label'] if x not in ('mean', '1', '2', '3', 'rsd', 'sd')]
        df1= df1[df1['label'].isin(xx)]
        df1= df1[df1['label'] != 'label']
        df1.iloc[:, 3:]= df1.iloc[:, 3:].astype(float).interpolate(method='linear', limit_direction='both', axis=0)
        df1= df1.iloc[:, 2:]
        df1= df1.set_index('label')
        ok= [x for x in df1.columns if x not in ('115in')]
        df9= df1[ok]
        for i in df9.columns:
            df1[i]= df1[i]/df1['115in']
        df1= df1.reset_index()
        return df1


    def cal_file(self):
        df1= pd.read_excel(self.input_files['ppm'])
        df1.columns= [x.lower() for x in df1.columns]
        df1.columns= [re.sub(' ', '', x) for x in df1.columns]
        df1.columns= [x.strip('(keds)') for x in df1.columns]
        df1= df1.dropna(how = 'all')
        df1['label']= df1.iloc[:, 0:1]
        df1= df1.iloc[:, 1:]
        df1['label']= df1['label'].astype(str)
        df1['label']= [x.lower() for x in df1['label']]
        df1['label']= [re.sub(' ', '', x) for x in df1['label']]
        df1['label']= [re.sub(r'\W+', '', x) for x in df1['label']]
        df1= df1.set_index('label')
        df1= df1.interpolate(method='linear', limit_direction='both', axis=0)
        df1= df1.reset_index()
        return df1


    def make_curve(self):
        data= self.normalize_quantitation()
        cal = self.cal_file()
        points= data[data['label'].isin(cal['label'])]
        sample= data[~data['label'].isin(cal['label'])]
        return points, sample


    def get_intercept(self):
        p1, _ =  self.make_curve()
        p2= p1.loc[:, p1.columns != 'label']
        p2= p2.applymap(lambda x: float(x))
        p2['label']= p1['label']
        p2= p2.groupby('label').transform('mean')
        p2['label']= p1['label']
        p2= p2.drop_duplicates(subset= ['label'])
        ll= set([x for x in p2.columns])
        cal = self.cal_file()
        pp= [x for x in cal.columns]
        mm= ll.intersection(pp)
        iterator_list= [x for x in mm if not x in ('label', '115in')]
        return p2, cal, iterator_list


    def plotting(self):

        xx, yy, zz= self.get_intercept()
        self.result_files['names']= zz
        df= pd.DataFrame()
        list1= []
        list2= []
        list3= []
        for x in zz:

            m, b = np.polyfit(xx[x].tolist(), yy[x].tolist(), 1)
            fig = plt.figure()
            plt.plot(xx[x], yy[x], linestyle='--', marker='o', color='b')
            plt.xlabel('area values normalized with int115')
            plt.ylabel('ppb values from cal ivs')
            plt.title(f'Calibration plot for {x}')
            self.result_image[x]= fig
            list1.append(x)
            list2.append(m)
            list3.append(b)
        df['label']= list1
        df['slope'] = list2
        df['intercept']= list3
        return df


    def extrapolate(self):
        cal = self.plotting()
        _, sam= self.make_curve()
        mm= [x for x in sam['label'] if x.startswith('lod')]
        sam= sam[~sam['label'].isin(mm)]
        mm= [x for x in sam['label'] if x.startswith('blank')]
        sam= sam[~sam['label'].isin(mm)]
        sam= sam.set_index('label')
        old_names = sam[sam.index.duplicated()].index.values
        new_names = sam[sam.index.duplicated()].index.values + "_dp"
        dictionary = dict(zip(old_names, new_names))
        xx= sam.loc[sam.index.duplicated(),:].rename(dictionary, axis= 0)
        sam= pd.concat([sam, xx])
        sam= sam[~sam.index.duplicated()]
        sam= sam.T
        cal= cal.set_index('label')
        sam= sam.merge(cal, how= 'inner', left_index= True, right_index= True)
        p1= sam.iloc[:, 0:-2]
        xx= p1.columns.tolist()
        from collections import Counter
        xx= Counter(xx)
        res= [k for k,v in xx.items() if v> 1]
        for i in p1.columns:
            sam[i]= sam[i] * sam['slope']
        sam.index= [x.upper() for x in sam.index]
        self.result_files['result']= sam
        self.result_files['calibration']= cal



if __name__ == "__main__":
    q1= Quantitation('sample.xlsx', 'cal.xlsx')
    q1.extrapolate()
