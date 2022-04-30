# -*- coding: utf-8 -*-
"""
Created on Fri Apr 29 09:47:20 2022

@author: yuki
"""

#FEM




"""

このプログラムは、後藤先生のfortranのプログラムをpythonで書き直したものです。

目標
numpyで行列計算を高速に
0での初期化を一瞬で
行列の内積をforで回さずに一瞬で
変数名は元のプとグラムを踏襲
変数型はこちらで指定



#今後
コメント多め
GPU
マルチスレッド
numba
疎行列 
class
わざわざ入れ替えずに直接行列式を解く
メッシュの可視化


参考
https://qiita.com/damyarou/items/8ca3432f9bba20a1f5ea
http://nkl.cc.u-tokyo.ac.jp/12w/CW-intro/CW-intro01.pdf
https://ipsj.ixsq.nii.ac.jp/ej/?action=repository_action_common_download&item_id=75552&item_no=1&attribute_id=1&file_no=1




#その他
!でのコメントアウトを#に変更、データ読み込み時も。
最初に配列を確保しなくていい
配列でデフォで行優先なのでfortranとメモリ確保の仕方が違う

fortranは配列は1始まりだが、pythonは0始まり。さらに[1:3]はfortranは[1,2,3]、pythonは[1,2]

floatで定義した配列にはstrを代入しても数値に代わるが、ただの変数はstrのままなので変換が必要

node番号!=配列番号

疑問点：境界以外の内部については、すべて荷重0かもしくはあたえられているという認識でいいのか？

"""


import numpy as np
from matplotlib import pyplot as plt



#デフォでmode=`r`
#pythonではすべて大文字の変数は定数扱いなので小文字に変換
#https://qiita.com/naomi7325/items/4eb1d2a40277361e898b    
#fortranは大文字小文字の区別なし

#withを使うと自動でcloseされる
#入力データに!を使ったコメントアウトがあるので分割して取得後、空白含むstrをintに変換
#pythonのfloatは64bit倍精度

#fortranでは単精度では1.23e4、倍精度では1.23d4とかくが、pythonはeのみ対応。よって置換
#https://docs.python.org/ja/3/library/functions.html#float

with open('input_AnalysisConditions.txt') as f:
    l = f.readlines()
    num_node  = int(l[0].split('!')[0]) #モデル節点数
    num_eleme = int(l[1].split('!')[0]) #モデル要素数
    thickness = float(l[2].split('!')[0].replace('d','e')) #モデル厚さ
    num_fix   = int(l[3].split('!')[0]) #拘束点数
    num_force = int(l[4].split('!')[0]) #荷重点数
    amp       = float(l[5].split('!')[0].replace('d','e')) #変形図倍率














#input (NUM_NODE, NUM_ELEME, NUM_FIX, NUM_FORCE, node, eleme, fix_pnt, force_pnt, fix, force)




#numpy.zeros(shape, dtype=float, order='C')
#order : {‘C’, ‘F’},多次元配列を行優先 (C-style) か列優先 (Fortran-style) でメモリに格納するかを指定します。  デフォでC  
#dtypedata-type, optionalDesired output data-type for the array, e.g, numpy.int8. Default is numpy.float64.
#https://numpy.org/doc/stable/reference/generated/numpy.zeros.html


#node = np.zeros((num_node,2),dtype=np.float64)
#emptyのほうがより高速だが、初期化されない
node      = np.empty((num_node,2), dtype=np.float64) #節点座標
eleme     = np.empty((num_eleme,3),dtype=np.int32) #各要素のコネクティビティ #つまりある三角形elementを構成する接点node番号(1スタートに注意)
fix_pnt   = np.empty((num_fix,2),  dtype=np.int32) #変位境界条件
force_pnt = np.empty((num_force,2),dtype=np.int32) #力学的境界条件 #接点番号と向きの配列
fix       = np.empty((num_fix),    dtype=np.float64) #変位境界条件の値
force     = np.empty((num_force),  dtype=np.float64) #力学的境界条件の値


#dを使った指数表現でない？
with open('input_point.txt') as f:
    l = f.readlines()
    for i, input_point in enumerate(l):
        node[i] = input_point.split(',')[1:3]
        

with open('input_eleme.txt') as f:
    l = f.readlines()
    for i, input_eleme in enumerate(l):
        eleme[i] = input_eleme.split(',')[1:4]

         
#行の最後に文章があるので行番号を厳密に指定        
with open('input_fixednodes.txt') as f:
    l = f.readlines()
    for i in range(num_fix):
        fix_pnt[i] = l[i].split()[1:3]
        fix[i] = l[i].split()[3].replace('d','e')
        

#行の最後に文章があるので行番号を厳密に指定        
with open('input_forcednodes.txt') as f:
    l = f.readlines()
    for i in range(num_force):
        force_pnt[i] = l[i].split()[1:3]
        force[i] = l[i].split()[3].replace('d','e')



print("Finish reading input text")





#メッシュの可視化
#https://qiita.com/itotomball/items/e63039d186fa1f564513
#接点番号は1から、pythonの行番号は0から始まるので修正
triangles = eleme -1
#各メッシュの値。今回はないので0
C = np.zeros(num_eleme)
fig = plt.figure(figsize=(8.0,3.0))
ax = fig.add_subplot()
fig.suptitle("input mesh")
#cmapについてはこちら
#https://beiznotes.org/matplot-cmap-list/
tpc = ax.tripcolor(node[:,0], node[:,1], triangles, C, edgecolors='black', cmap='jet')
# カラーバーを表示
fig.colorbar(tpc)
# アスペクト比を1対1に, レイアウトを調整
ax.set_aspect('equal')
fig.tight_layout()
plt.show()
#fig.savefig('input_mesh.png')









#makeDmat (Dmat)

#配列の初期化
Dmat = np.zeros((3,3),dtype=np.float64) #弾性剛性マトリックス
  
with open('input_matinfo.txt') as f:
    l = f.readlines()
    Young = float(l[0].split('!')[0].replace('d','e'))
    Poisson = float(l[1].split('!')[0].replace('d','e'))


print('YOUNG''S MODULUS [Pa] :', Young)
print('POISSON''S RATIO :', Poisson)  


#排列がpythonでは0始まりなので[0,1]は1行2列、fortranでは[1,2]とかく。

#平面応力状態 P.121 式(5.53)
Dmat[0,0] = Young / (1 - (Poisson ** 2))
Dmat[0,1] = Young / (1 - (Poisson ** 2)) * Poisson
Dmat[1,0] = Young / (1 - (Poisson ** 2)) * Poisson
Dmat[1,1] = Young / (1 - (Poisson ** 2))
Dmat[2,2] = Young / (1 - (Poisson ** 2)) * (1- Poisson) / 2

#平面ひずみ状態 P.122 式(5.54)
#Dmat[0,0] = Young * (1 - Poisson) / (1 - 2 * Poisson) / (1 + Poisson)
#Dmat[0,1] = Young / (1 - 2 * Poisson) / (1 + Poisson) * Poisson
#Dmat[1,0] = Young / (1 - 2 * Poisson) / (1 + Poisson) * Poisson
#Dmat[1,1] = Young * (1 - Poisson) / (1 - 2 * Poisson) / (1 + Poisson)
#Dmat[2,2] = Young / (1 + Poisson) / 2






#----------------------------------
#ouptputを今は書いていない


print('MAKE D-MATRIX')



























# makeBmat (NUM_NODE, NUM_ELEME, node, eleme, Bmat, Ae)


#配列の初期化
Bmat   = np.zeros((3,6,num_eleme), dtype=np.float64) #Bマトリックス（形状関数の偏微分）
Ae     = np.zeros((num_eleme), dtype=np.float64) #要素面積
e_node = np.empty((3,2), dtype=np.float64) #不明　ある三角形elementを構成する3接点のxy座標




#各要素の面積を求める

#配列0始まりに変更
#eleme[i,j]は接点番号であり、pythonにおける配列位置にするためには-1する必要あり
for i in range(num_eleme):
    for j in range(3):
        e_node[j,0] = node[eleme[i,j]-1,0]
        e_node[j,1] = node[eleme[i,j]-1,1]
    
    #P.102 式(5.19)
    Ae[i] = 0.5 * ((e_node[0,0] * (e_node[1,1] - e_node[2,1])) + (e_node[1,0] * (e_node[2,1] - e_node[0,1]))  + (e_node[2,0] * (e_node[0,1] - e_node[1,1])))


#各要素のB-matrixを求める
#配列0始まりに変更
#eleme[i,j]は接点番号であり、pythonにおける配列位置にするためには-1する必要あり
for i in range(num_eleme):
    for j in range(3):
        e_node[j,0] = node[eleme[i,j]-1,0]
        e_node[j,1] = node[eleme[i,j]-1,1]




    #P.129 式(5.77)
    #配列0始まりに変更
    Bmat[0,0,i] = (1 / (2 * Ae[i])) * (e_node[1,1] - e_node[2,1])
    Bmat[0,2,i] = (1 / (2 * Ae[i])) * (e_node[2,1] - e_node[0,1])
    Bmat[0,4,i] = (1 / (2 * Ae[i])) * (e_node[0,1] - e_node[1,1])
    
    Bmat[1,1,i] = (1 / (2 * Ae[i])) * (e_node[2,0] - e_node[1,0])
    Bmat[1,3,i] = (1 / (2 * Ae[i])) * (e_node[0,0] - e_node[2,0])
    Bmat[1,5,i] = (1 / (2 * Ae[i])) * (e_node[1,0] - e_node[0,0])
    
    Bmat[2,0,i] = (1 / (2 * Ae[i])) * (e_node[2,0] - e_node[1,0])
    Bmat[2,1,i] = (1 / (2 * Ae[i])) * (e_node[1,1] - e_node[2,1])
    Bmat[2,2,i] = (1 / (2 * Ae[i])) * (e_node[0,0] - e_node[2,0])
    Bmat[2,3,i] = (1 / (2 * Ae[i])) * (e_node[2,1] - e_node[0,1])
    Bmat[2,4,i] = (1 / (2 * Ae[i])) * (e_node[1,0] - e_node[0,0])
    Bmat[2,5,i] = (1 / (2 * Ae[i])) * (e_node[0,1] - e_node[1,1])


#----------------------------------
#ouptputを今は書いていない

print('MAKE B-MATRIX')




















# makeKmat (NUM_NODE, NUM_ELEME, eleme, Bmat, Dmat, Kmat, Ae, THICKNESS)




#配列の初期化
Kmat   = np.zeros((2*num_node,2*num_node), dtype=np.float64) #全体剛性マトリックス
e_Kmat = np.zeros((6,6), dtype=np.float64)  #要素剛性マトリックス

#定数になってしまうのでTをtに変更
BtD    = np.zeros((6,3), dtype=np.float64)  #
BtDB   = np.zeros((6,6), dtype=np.float64)  #

for i in range(num_eleme):
    #要素剛性マトリックスの構築 P.135 式(5.94)
    BtD = np.dot(Bmat[:,:,i].T, Dmat)
    BtDB = np.dot(BtD, Bmat[:,:,i])
    e_Kmat = Ae[i] * thickness * BtDB 
    
    #全体剛性マトリックスへの組込み P.137 式(5.97)

    #ここもっと行列計算したい
    for j in range(3):
        for k in range(3):

            #eleme[i,j]は接点番号であり、pythonにおける配列位置にするためには-1する必要があると思ったが、
            #Kmatの式の作り方からやめておく
            pt1 = eleme[i,j] #-1 #行
            pt2 = eleme[i,k] #-1 #列
            
            #[2x2]の成分ごとに組込み
            #j,lがpythonでは0スタートなので-1を消したり+2を+1にしたり
                        #Kmat[2*(pt1-1), 2*(pt2-1)] += e_Kmat[2*j, 2*k]
            #Kmat[2*(pt1-1), 2*(pt2-1)+1] += e_Kmat[2*j, 2*k+1]
            #Kmat[2*(pt1-1)+1, 2*(pt2-1)] += e_Kmat[2*j+1, 2*k]
            #Kmat[2*(pt1-1)+1, 2*(pt2-1)+1] += e_Kmat[2*j+1, 2*k+1]
            
            #1行でできる
            Kmat[2*(pt1-1):2*(pt1-1)+2, 2*(pt2-1):2*(pt2-1)+2] += e_Kmat[2*j:2*j+2, 2*k:2*k+2]



print( 'MAKE K-MATRIX')




#疎行列の可視化
fig = plt.figure()
ax = fig.add_subplot()
fig.suptitle("Kmat")
ax.spy(Kmat)
# アスペクト比を1対1に, レイアウトを調整
#ax.set_aspect('equal')
fig.tight_layout()
plt.show()
#fig.savefig('Kmat.png')





# makeFmat (NUM_NODE, NUM_FORCE, Fmat, force_pnt, force)


Fmat = np.zeros((2*num_node), dtype=np.float64) #節点荷重ベクトル


for i in range(num_force):
    #force_pnt[i,1]は接点番号であり、pythonにおける配列位置にするために変更、
    #各接点のx,yの順に配列が並んでいるので、xは+1、yは+2が割り振られうまく位置を計算している。
    #pythonの配列番号0始まりに変更
    Fmat[2*(force_pnt[i,0]-1) + force_pnt[i,1] -1] = force[i]
    
    if (force_pnt[i,1] != 1 and force_pnt[i,1] != 2):
        print('INPUT DATA "input_forcednodes.txt" IS NOT APPROPREATE.')
        print('load direction is now',force_pnt[i,2], ', not 1(x) or 2(y)' )
        break
 


#output省略













# makeUmat (NUM_NODE, NUM_FIX, Umat, fix_pnt, fix)



Umat = np.zeros((2*num_node), dtype=np.float64)



for i in range(num_force):
    #force_pnt[i,1]は接点番号であり、pythonにおける配列位置にするために変更、
    #各接点のx,yの順に配列が並んでいるので、xは+1、yは+2が割り振られうまく位置を計算している。
    #pythonの配列番号0始まりに変更
    Umat[2*(fix_pnt[i,0]-1) + fix_pnt[i,1] -1] = fix[i]
    
    if (fix_pnt[i,1] != 1 and fix_pnt[i,1] != 2):
        print('IINPUT DATA "input_fixednodes.txt" IS NOT APPROPREATE.')
        print('Fixed direction is now', fix_pnt[i,2], ', not 1(x) or 2(y)' )
        break


#output省略、というか解けていないから不必要











# makeSUBmatrix (NUM_NODE, NUM_FIX, Kmat, Fmat, Umat, fix_pnt, known_DOF, unknown_DOF, K11, K12, K22, F1, F2, U1, U2)



#境界条件適用後の小行列を作成
known_DOF   = np.empty(num_fix, dtype=np.int32)              #既知節点変位ベクトルの自由度  #既知接点変位の行番号であり、未知荷重行に対応
unknown_DOF = np.empty(2*num_node - num_fix, dtype=np.int32) #未知節点変位ベクトルの自由度

K11 = np.zeros((2*num_node-num_fix, 2*num_node-num_fix), dtype=np.float64) #変位境界条件付加後の小行列
K12 = np.zeros((2*num_node-num_fix, num_fix), dtype=np.float64)            #変位境界条件付加後の小行列 #K21の転置
K22 = np.zeros((num_fix, num_fix), dtype=np.float64)                       #変位境界条件付加後の小行列
F1  = np.zeros((2*num_node-num_fix), dtype=np.float64)                     #変位境界条件付加後の小行列 #与えられる
F2  = np.zeros(num_fix, dtype=np.float64)                                  #変位境界条件付加後の小行列
U1  = np.zeros((2*num_node-num_fix), dtype=np.float64)                     #変位境界条件付加後の小行列
U2  = np.zeros(num_fix, dtype=np.float64)                                  #変位境界条件付加後の小行列　#与えられる



##既知接点変位の行番号配列作成
#pythonの配列番号0始まりに変更
#各接点のx,yの順に配列が並んでいるので、xは+1、yは+2が割り振られうまく位置を計算している。
for i in range(num_fix):
    known_DOF[i] = 2*(fix_pnt[i,0]-1) + fix_pnt[i,1] -1



"""
#何やっているかわからないが、おそらく決まっていない行番号の一覧を作成
DO j=1, known_DOF(1)-1
  unknown_DOF(j) = j
END DO


DO i=2, NUM_FIX
  DO j=known_DOF(i-1)+1, known_DOF(i)-1
    unknown_DOF(j-(i-1)) = j
  END DO
END DO


DO j=known_DOF(NUM_FIX)+1, 2*NUM_NODE
  unknown_DOF(j-NUM_FIX) = j
END DO

"""

num = 0
for j in range(2*num_node):
    if j not in known_DOF:
        unknown_DOF[num] = j
        num += 1
        

#行列の変形、線形代数を復習したほうが良さそう
for i in range(2*num_node-num_fix):
    for j in range(2*num_node-num_fix):
        K11[i,j] = Kmat[unknown_DOF[i], unknown_DOF[j]]
    for j in range(num_fix):
        K12[i,j] = Kmat[unknown_DOF[i], known_DOF[j]]
        
    F1[i] = Fmat[unknown_DOF[i]]
    U1[i] = Umat[unknown_DOF[i]] #未知成分


for i in range(num_fix):
    for j in range(num_fix):
        K22[i,j] = Kmat[known_DOF[i], known_DOF[j]]
        
    F2[i] = Fmat[known_DOF[i]] #未知成分
    U2[i] = Umat[known_DOF[i]] 



print('MAKE SUB-MATRIX')
















# makeInverse (NUM_NODE, NUM_FIX, K11)

# 逆行列のアルゴリズムがわからない。

#test ちゃんと単位行列になるか
#K11inv = np.linalg.inv(K11)
#a = np.dot(K11inv, K11)


#K11を上書きして逆行列
K11 = np.linalg.inv(K11)






# solveUmat (NUM_NODE, NUM_FIX, Umat, K11, K12, F1, U1, U2, unknown_DOF)


#U1  = np.zeros((2*num_node-num_fix), dtype=np.float64)   #変位境界条件付加後の小行列 #前に作成済み
fku = np.zeros((2*num_node-num_fix), dtype=np.float64)   #わからない   (F-Kd) #大文字から小文字に変更

#P.139 式(5.104)
#一気に計算する
fku = F1 - np.dot(K12, U2)

#K11は逆行列をすでにとっている。
#U1は未知成分だったが、ここで判明
U1 = np.dot(K11, fku)

#もっとパイソニックに書きたい
#元の並びのUmatに、判明部分を代入
for i in range(2*num_node-num_fix):
    Umat[unknown_DOF[i]] = U1[i]



#output省略

print('SOLVE U-MATRIX')







# solveFmat(NUM_NODE, NUM_FIX, Fmat, K12, K22, F2, U1, U2, known_DOF)

#P.140

#K21=K12.T 対称性より
#F2は未知成分だったが、ここで判明
F2 = np.dot(K12.T, U1) + np.dot(K22, U2)


#もっとパイソニックに書きたい
#元の並びのUmatに、判明部分を代入
for i in range(num_fix):
    Fmat[known_DOF[i]] = F2[i]

#output省略

print('SOLVE F-MATRIX')







# displacement (NUM_NODE, AMP, node, Umat)


disp = np.zeros((num_node, 2), dtype=np.float64)  #amp倍した変位後の座標


#もう少しうまく書きたい
for i in range(num_node):
    disp[i,0] = node[i,0] + Umat[2*i] * amp
    disp[i,1] = node[i,1] + Umat[2*i+1] * amp

#output省略



print('CALCULATE DISPLACEMENT')










# distribution (NUM_NODE, NUM_ELEME, eleme, Bmat, Dmat, Umat)


strain = np.zeros((3, num_eleme), dtype=np.float64)  #各三角形のひずみ(εx,εy,γxy)
stress = np.zeros((3, num_eleme), dtype=np.float64)  #各三角形のの応力(σx,σy,τxy)
e_Umat = np.empty(6, dtype=np.float64)               #ある三角形要素の変位


for i in range(num_eleme):
    for j in range(3):
        e_Umat[2*j]   = Umat[2*(eleme[i,j]-1)]     #三角形要素のx変位
        e_Umat[2*j+1] = Umat[2*(eleme[i,j]-1)+1]   #三角形要素のy変位

    strain[:,i] = np.dot(Bmat[:,:,i], e_Umat)
    stress[:,i] = np.dot(Dmat, strain[:,i])


print('CALCULATE DISTRIBUTIONS')


#output省略








#可視化
#https://qiita.com/itotomball/items/e63039d186fa1f564513


result_list = (('strain_x', strain[0]),('strain_y', strain[1]),('strain_xy', strain[2]),('stress_x', stress[0]),('stress_y', stress[1]),('stress_xy', stress[2]))
for title, C in result_list:


    #接点番号は1から、pythonの行番号は0から始まるので修正
    triangles = eleme -1
    fig = plt.figure(figsize=(8.0,3.0))
    ax = fig.add_subplot()

    fig.suptitle(title)
    #cmapについてはこちら
    #https://beiznotes.org/matplot-cmap-list/
    tpc = ax.tripcolor(disp[:,0], disp[:,1], triangles, C, edgecolors='black', cmap='jet')
    # カラーバーを表示
    fig.colorbar(tpc)
    # アスペクト比を1対1に, レイアウトを調整
    ax.set_aspect('equal')
    plt.show()
    #fig.savefig(f'result_{title}.png')
    
    
    
    
    
#メモリ確認
#http://harmonizedai.com/article/%E5%A4%89%E6%95%B0%E3%81%AE%E3%83%A1%E3%83%A2%E3%83%AA%E5%86%85%E5%AE%B9%E3%82%92%E4%B8%80%E8%A6%A7%E8%A1%A8%E7%A4%BA%E3%81%97%E3%81%A6/
import sys

print("{}{: >15}{}{: >10}{}".format('|','Variable Name','|','Memory','|'))
print(" ------------------------------------ ")
for var_name in dir():
    if not var_name.startswith("_"):
        print("{}{: >15}{}{: >10}{}".format('|',var_name,'|',sys.getsizeof(eval(var_name)),'|'))

