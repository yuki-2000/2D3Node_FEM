# Basic_2D3Node_FEM
 Pythonで書かれたFEMプログラム


# Version1.0.0 概要

最初のバージョンです。
基本的には元となった`2D-CST_v1-1.F90`ファイルをpythonに移行したものです。

## 追加点
メッシュの可視化機能
疎行列の可視化機能
結果の可視化機能

## 非実装
各matrixの出力は、SpyderのVariable Explorerで可能であり、またフォーマットが大変なので行っていません。
最終的な`output_disp.dat`、`output_strain.dat`、`output_stress.dat`の出力に関しては、
smartGRAPHなどの可視化ソフトで別で行うかもしれないので、後々実装するかもしれません。


## Pythonの利点

行列計算が1行で済む（積、逆行列）
初期化が簡単
変数を何度も書かなくてもよい
計算時に型を考えなくて良い

## FortranからPythonへの移行時の注意
Fortranのコメントアウトは`!`
Fortranの配列は1から始まる
Fortranの倍精度は`1.23d4`というように、`d`を使用する。

詳しくはプログラム内のコメントで




## その他

数式の可視化は
https://aotamasaki.hatenablog.com/entry/2020/08/09/github%E3%82%84note%E3%81%A7%E3%82%82TeX%E3%81%AE%E6%95%B0%E5%BC%8F%E3%82%92%E6%9B%B8%E3%81%8F%E3%81%9C




# 各解説

## 型宣言


pythonではすべて大文字の変数は定数扱いなので小文字に変換
https://qiita.com/naomi7325/items/4eb1d2a40277361e898b   

|      | Fortran | Python(numpy)| 意味 |
|:---|:---|:---|:---|
|整数  | INTEGER | np.int32 | 32bit |
|浮動小数  |    DOUBLE PRECISION  | np.float64  | 倍精度 64bit  |

https://jp.xlsoft.com/documents/intel/cvf/vf-html/pg/pg20.htm




numpy.zeros(shape, dtype=float, order='C')
order : {‘C’, ‘F’},多次元配列を行優先 (C-style) か列優先 (Fortran-style) でメモリに格納するかを指定します。  デフォでC  
dtypedata-type, optionalDesired output data-type for the array, e.g, numpy.int8. Default is numpy.float64.

https://numpy.org/doc/stable/reference/generated/numpy.zeros.html
https://numpy.org/doc/stable/reference/generated/numpy.empty.html#numpy.empty


浮動小数のdとe
fortranでは単精度では`1.23e4`、倍精度では`1.23d4`とかくが、pythonは`e`のみ対応。よって置換する必要がある。
https://docs.python.org/ja/3/library/functions.html#float



## データ読み取り

今回、txt形式の入力データを読み取る必要があるが、それぞれ書式が違う。


| ファイル名 | 区切り| 型  |その他  |内容 |
|:---|:---|:---|:---|:---|
|input_AnalysisConditions.txt |各行1要素　      |整数、浮動d小数 |!コメント |モデルの節点数など |
|input_point.txt                       |  カンマ区切り   |固定小数              |                |節点座標 |
|input_eleme.txt                      | カンマ区切り    |整数                     |                 |要素を構成する節点番号（1スタート）の集まり|
|input_fixednodes.txt              |スペース区切り |整数、浮動d小数  |   文末コメントあり| 変位境界条件   |
|input_forcednodes.txt           |スペース区切り |整数、浮動d小数  |     文末コメントあり| 荷重境界条件 |








### input_AnalysisConditions.txt

```
205     !モデル節点数
320     !モデル要素数
0.01d0  !モデル厚さ
10      !拘束点数
5       !荷重点数
1.0d0   !変形図倍率
```

readlines()で各行のリストにしてから、`split('!')[0]`で`!`より前を取得、`.replace('d','e')`で変換してから、その後`int()`や`float()`を使用して`str`から変換




## makeDmat

弾性剛性マトリックスDの作成


![\begin{equation}
 \sigma = D \epsilon
\end{equation}
](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Clarge+%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A+%5Csigma+%3D+D+%5Cepsilon%0A%5Cend%7Bequation%7D%0A)

#### 平面応力状態での応力ーひずみ関係式

![\begin{equation}
\begin{Bmatrix} \sigma_x \\ \sigma_y \\ \tau_{xy} \end{Bmatrix}
=\frac{E}{1-\nu^2}\begin{bmatrix} 1 & \nu & 0 \\ \nu & 1 & 0 \\ 0 & 0 & \cfrac{1-\nu}{2} \end{bmatrix}
\begin{Bmatrix} \epsilon_x \\ \epsilon_y \\ \gamma_{xy} \end{Bmatrix}
\end{equation}](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A%5Cbegin%7BBmatrix%7D+%5Csigma_x+%5C%5C+%5Csigma_y+%5C%5C+%5Ctau_%7Bxy%7D+%5Cend%7BBmatrix%7D%0A%3D%5Cfrac%7BE%7D%7B1-%5Cnu%5E2%7D%5Cbegin%7Bbmatrix%7D+1+%26+%5Cnu+%26+0+%5C%5C+%5Cnu+%26+1+%26+0+%5C%5C+0+%26+0+%26+%5Ccfrac%7B1-%5Cnu%7D%7B2%7D+%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D+%5Cepsilon_x+%5C%5C+%5Cepsilon_y+%5C%5C+%5Cgamma_%7Bxy%7D+%5Cend%7BBmatrix%7D%0A%5Cend%7Bequation%7D)

#### 平面ひずみ状態での応力ーひずみ関係式

![\begin{equation}
\begin{Bmatrix} \sigma_x \\ \sigma_y \\ \tau_{xy} \end{Bmatrix}
=\frac{E}{(1+\nu)(1-2\nu)}\begin{bmatrix} 1-\nu & \nu & 0 \\ \nu & 1-\nu & 0 \\ 0 & 0 & \cfrac{1-2\nu}{2} \end{bmatrix}
\begin{Bmatrix} \epsilon_x \\ \epsilon_y \\ \gamma_{xy} \end{Bmatrix}
\end{equation}
](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A%5Cbegin%7BBmatrix%7D+%5Csigma_x+%5C%5C+%5Csigma_y+%5C%5C+%5Ctau_%7Bxy%7D+%5Cend%7BBmatrix%7D%0A%3D%5Cfrac%7BE%7D%7B%281%2B%5Cnu%29%281-2%5Cnu%29%7D%5Cbegin%7Bbmatrix%7D+1-%5Cnu+%26+%5Cnu+%26+0+%5C%5C+%5Cnu+%26+1-%5Cnu+%26+0+%5C%5C+0+%26+0+%26+%5Ccfrac%7B1-2%5Cnu%7D%7B2%7D+%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D+%5Cepsilon_x+%5C%5C+%5Cepsilon_y+%5C%5C+%5Cgamma_%7Bxy%7D+%5Cend%7BBmatrix%7D%0A%5Cend%7Bequation%7D%0A)




## makeBmat

ひずみ変位マトリックスBを求める。

参考
https://qiita.com/damyarou/items/8ca3432f9bba20a1f5ea

形状関数Nについて、三角形要素(CST要素)での任意の点の変位は以下のようにあらわすことができる。
（要素内の座標はNに含まれている。）

![\begin{equation}
\begin{Bmatrix} u \\ v \end{Bmatrix}
=[\boldsymbol{N_e}]\{\boldsymbol{d_e}\}
=\begin{bmatrix}
N_i & 0   & N_j & 0   & N_k & 0   \\
0   & N_i & 0   & N_j & 0   & N_k
\end{bmatrix}
\begin{Bmatrix} u_1 \\ v_1 \\ u_2\\ v_2 \\u_3 \\v_3 \end{Bmatrix}
\end{equation}
](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A%5Cbegin%7BBmatrix%7D+u+%5C%5C+v+%5Cend%7BBmatrix%7D%0A%3D%5B%5Cboldsymbol%7BN_e%7D%5D%5C%7B%5Cboldsymbol%7Bd_e%7D%5C%7D%0A%3D%5Cbegin%7Bbmatrix%7D%0AN_i+%26+0+++%26+N_j+%26+0+++%26+N_k+%26+0+++%5C%5C%0A0+++%26+N_i+%26+0+++%26+N_j+%26+0+++%26+N_k%0A%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D+u_1+%5C%5C+v_1+%5C%5C+u_2%5C%5C+v_2+%5C%5Cu_3+%5C%5Cv_3+%5Cend%7BBmatrix%7D%0A%5Cend%7Bequation%7D%0A)

よって、ひずみを求めるために偏微分をすると、ちょうど定数行列となる。

![\begin{equation}
\boldsymbol{\epsilon}=
\begin{Bmatrix}
\cfrac{\partial u}{\partial x} \\
\cfrac{\partial v}{\partial y} \\
\cfrac{\partial u}{\partial y}+\cfrac{\partial v}{\partial x}
\end{Bmatrix}
=\begin{bmatrix}
\cfrac{\partial N_i}{\partial x} & 0 & \cfrac{\partial N_j}{\partial x} & 0 & \cfrac{\partial N_k}{\partial x} & 0 \\
0 & \cfrac{\partial N_i}{\partial y} & 0 & \cfrac{\partial N_j}{\partial y} & 0 & \cfrac{\partial N_k}{\partial y} \\
\cfrac{\partial N_i}{\partial y} & \cfrac{\partial N_i}{\partial x} &
\cfrac{\partial N_j}{\partial y} & \cfrac{\partial N_j}{\partial x} &
\cfrac{\partial N_k}{\partial y} & \cfrac{\partial N_k}{\partial x}
\end{bmatrix}
\begin{Bmatrix} u_1 \\ v_1 \\ u_2\\ v_2 \\u_3 \\v_3 \end{Bmatrix}
=[\boldsymbol{B_e}]\{\boldsymbol{d_e}\}
\end{equation}](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A%5Cboldsymbol%7B%5Cepsilon%7D%3D%0A%5Cbegin%7BBmatrix%7D%0A%5Ccfrac%7B%5Cpartial+u%7D%7B%5Cpartial+x%7D+%5C%5C%0A%5Ccfrac%7B%5Cpartial+v%7D%7B%5Cpartial+y%7D+%5C%5C%0A%5Ccfrac%7B%5Cpartial+u%7D%7B%5Cpartial+y%7D%2B%5Ccfrac%7B%5Cpartial+v%7D%7B%5Cpartial+x%7D%0A%5Cend%7BBmatrix%7D%0A%3D%5Cbegin%7Bbmatrix%7D%0A%5Ccfrac%7B%5Cpartial+N_i%7D%7B%5Cpartial+x%7D+%26+0+%26+%5Ccfrac%7B%5Cpartial+N_j%7D%7B%5Cpartial+x%7D+%26+0+%26+%5Ccfrac%7B%5Cpartial+N_k%7D%7B%5Cpartial+x%7D+%26+0+%5C%5C%0A0+%26+%5Ccfrac%7B%5Cpartial+N_i%7D%7B%5Cpartial+y%7D+%26+0+%26+%5Ccfrac%7B%5Cpartial+N_j%7D%7B%5Cpartial+y%7D+%26+0+%26+%5Ccfrac%7B%5Cpartial+N_k%7D%7B%5Cpartial+y%7D+%5C%5C%0A%5Ccfrac%7B%5Cpartial+N_i%7D%7B%5Cpartial+y%7D+%26+%5Ccfrac%7B%5Cpartial+N_i%7D%7B%5Cpartial+x%7D+%26%0A%5Ccfrac%7B%5Cpartial+N_j%7D%7B%5Cpartial+y%7D+%26+%5Ccfrac%7B%5Cpartial+N_j%7D%7B%5Cpartial+x%7D+%26%0A%5Ccfrac%7B%5Cpartial+N_k%7D%7B%5Cpartial+y%7D+%26+%5Ccfrac%7B%5Cpartial+N_k%7D%7B%5Cpartial+x%7D%0A%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D+u_1+%5C%5C+v_1+%5C%5C+u_2%5C%5C+v_2+%5C%5Cu_3+%5C%5Cv_3+%5Cend%7BBmatrix%7D%0A%3D%5B%5Cboldsymbol%7BB_e%7D%5D%5C%7B%5Cboldsymbol%7Bd_e%7D%5C%7D%0A%5Cend%7Bequation%7D)


よってひずみ変位マトリックスBは以下のように計算できる。

![\begin{align}
[\boldsymbol{B}]
=\frac{1}{2\Delta}
\begin{bmatrix}
b_i & 0   & b_j & 0   & b_k & 0   \\
0   & c_i & 0   & c_j & 0   & c_k \\
c_i & b_i & c_j & b_j & c_k & b_k \\
\end{bmatrix}
=\frac{1}{2\Delta}
\begin{bmatrix}
y_j-y_k & 0       & y_k-y_i & 0       & y_i-y_j & 0       \\
0       & x_k-x_j & 0       & x_i-x_k & 0       & x_j-x_i \\
x_k-x_j & y_j-y_k & x_i-x_k & y_k-y_i & x_j-x_i & y_i-y_j
\end{bmatrix} \\
\Delta=&1/2\cdot[(x_k-x_j)y_i+(x_i-x_k)y_j+(x_j-x_i)y_k] \qquad \text{(Element area)}
\end{align}](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Balign%7D%0A%5B%5Cboldsymbol%7BB%7D%5D%0A%3D%5Cfrac%7B1%7D%7B2%5CDelta%7D%0A%5Cbegin%7Bbmatrix%7D%0Ab_i+%26+0+++%26+b_j+%26+0+++%26+b_k+%26+0+++%5C%5C%0A0+++%26+c_i+%26+0+++%26+c_j+%26+0+++%26+c_k+%5C%5C%0Ac_i+%26+b_i+%26+c_j+%26+b_j+%26+c_k+%26+b_k+%5C%5C%0A%5Cend%7Bbmatrix%7D%0A%3D%5Cfrac%7B1%7D%7B2%5CDelta%7D%0A%5Cbegin%7Bbmatrix%7D%0Ay_j-y_k+%26+0+++++++%26+y_k-y_i+%26+0+++++++%26+y_i-y_j+%26+0+++++++%5C%5C%0A0+++++++%26+x_k-x_j+%26+0+++++++%26+x_i-x_k+%26+0+++++++%26+x_j-x_i+%5C%5C%0Ax_k-x_j+%26+y_j-y_k+%26+x_i-x_k+%26+y_k-y_i+%26+x_j-x_i+%26+y_i-y_j%0A%5Cend%7Bbmatrix%7D+%5C%5C%0A%5CDelta%3D%261%2F2%5Ccdot%5B%28x_k-x_j%29y_i%2B%28x_i-x_k%29y_j%2B%28x_j-x_i%29y_k%5D+%5Cqquad+%5Ctext%7B%28Element+area%29%7D%0A%5Cend%7Balign%7D)



### プログラム解説

`enode`は要素を構成する節点の座標。
各要素(iで指定)ごとに作られる。
|　|    | 
|:---|:---|
| 1節点目x   | 1節点目y   |   
| 2節点目x   | 2節点目y   |   
| 3節点目x   | 3節点目y   |   

`eleme[i,j]`が要素iを構成する節点のうちj番目の`節点番号`を返す
`node[i,j]`はi番目の節点のx(j=0)、y(j=2)を返す。
`Bmat`は、`3x6x要素数`のarrayとなっている。すなわち、`Bmat[:,:,i]`でi要素のBマトリクスである。



## makeKmat

全体剛性マトリクスKの作成

厚さ`h`が一定値であり、Bマトリクスが三角形要素の時は定数のため、
__ある要素element__ において、弱形式より以下が成り立つ。

![\begin{equation}
[\boldsymbol{K_e}]=\int_A[\boldsymbol{B_e}]^T[\boldsymbol{D_e}][\boldsymbol{B_e}]hdA=h\cdot\Delta\cdot[\boldsymbol{B_e}]^T[\boldsymbol{D_e}][\boldsymbol{B_e}]
\end{equation}](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A%5B%5Cboldsymbol%7BK_e%7D%5D%3D%5Cint_A%5B%5Cboldsymbol%7BB_e%7D%5D%5ET%5B%5Cboldsymbol%7BD_e%7D%5D%5B%5Cboldsymbol%7BB_e%7D%5DhdA%3Dh%5Ccdot%5CDelta%5Ccdot%5B%5Cboldsymbol%7BB_e%7D%5D%5ET%5B%5Cboldsymbol%7BD_e%7D%5D%5B%5Cboldsymbol%7BB_e%7D%5D%0A%5Cend%7Bequation%7D)

![\begin{equation}
 K_e d_e =F_e \\
\end{equation}](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A+K_e+d_e+%3DF_e+%5C%5C%0A%5Cend%7Bequation%7D)


例えば、節点[200,204,205]で構成されるelementについて、以下が成り立つ。




![\begin{equation}
\begin{bmatrix}
k_11 & k_12 & k_13 & k_14 & k_15 & k_16 \\
k_21 & k_22 & k_23 & k_24 & k_25 & k_26 \\
k_31 & k_32 & k_33 & k_34 & k_35 & k_36 \\
k_41 & k_42 & k_43 & k_44 & k_45 & k_46 \\
k_51 & k_52 & k_53 & k_54 & k_55 & k_56 \\
k_61 & k_62 & k_63 & k_54 & k_65 & k_66
\end{bmatrix}
\begin{Bmatrix} u_200 \\ v_200 \\ u_204\\ v_204 \\u_205 \\v_205 \end{Bmatrix}
=\begin{Bmatrix} F_{x200} \\  F_{y200} \\ F_{x204}\\ F_{y204} \\  F_{x205} \\  F_{y205} \end{Bmatrix}
\end{equation}](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A%5Cbegin%7Bbmatrix%7D%0Ak_11+%26+k_12+%26+k_13+%26+k_14+%26+k_15+%26+k_16+%5C%5C%0Ak_21+%26+k_22+%26+k_23+%26+k_24+%26+k_25+%26+k_26+%5C%5C%0Ak_31+%26+k_32+%26+k_33+%26+k_34+%26+k_35+%26+k_36+%5C%5C%0Ak_41+%26+k_42+%26+k_43+%26+k_44+%26+k_45+%26+k_46+%5C%5C%0Ak_51+%26+k_52+%26+k_53+%26+k_54+%26+k_55+%26+k_56+%5C%5C%0Ak_61+%26+k_62+%26+k_63+%26+k_54+%26+k_65+%26+k_66%0A%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D+u_200+%5C%5C+v_200+%5C%5C+u_204%5C%5C+v_204+%5C%5Cu_205+%5C%5Cv_205+%5Cend%7BBmatrix%7D%0A%3D%5Cbegin%7BBmatrix%7D+F_%7Bx200%7D+%5C%5C++F_%7By200%7D+%5C%5C+F_%7Bx204%7D%5C%5C+F_%7By204%7D+%5C%5C++F_%7Bx205%7D+%5C%5C++F_%7By205%7D+%5Cend%7BBmatrix%7D%0A%5Cend%7Bequation%7D)



これについて、例えば節点200の荷重について、以下が成り立つ。

![\begin{equation}
\begin{bmatrix}
k_11 & k_12  \\
k_21 & k_22 
\end{bmatrix}
\begin{Bmatrix} u_200 \\ v_200 \end{Bmatrix}
+\begin{bmatrix}
k_13 & k_14  \\
k_23 & k_24 
\end{bmatrix}
\begin{Bmatrix} u_204 \\ v_204 \end{Bmatrix}
+\begin{bmatrix}
k_15 & k_16 \\
k_25 & k_26 
\end{bmatrix}
\begin{Bmatrix} u_206 \\ v_206 \end{Bmatrix}
=\begin{Bmatrix} F_{x200} \\  F_{y200} \end{Bmatrix}
\end{equation}](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A%5Cbegin%7Bbmatrix%7D%0Ak_11+%26+k_12++%5C%5C%0Ak_21+%26+k_22+%0A%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D+u_200+%5C%5C+v_200+%5Cend%7BBmatrix%7D%0A%2B%5Cbegin%7Bbmatrix%7D%0Ak_13+%26+k_14++%5C%5C%0Ak_23+%26+k_24+%0A%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D+u_204+%5C%5C+v_204+%5Cend%7BBmatrix%7D%0A%2B%5Cbegin%7Bbmatrix%7D%0Ak_15+%26+k_16+%5C%5C%0Ak_25+%26+k_26+%0A%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D+u_206+%5C%5C+v_206+%5Cend%7BBmatrix%7D%0A%3D%5Cbegin%7BBmatrix%7D+F_%7Bx200%7D+%5C%5C++F_%7By200%7D+%5Cend%7BBmatrix%7D%0A%5Cend%7Bequation%7D)



全体の行列に組み込むと、以下のようになる。



![\begin{equation}
\begin{bmatrix}
     0       & \cdots     &    0        &        0       & \cdots  &       0   \\
\vdots & \ddots    & \vdots &   \vdots   & \ddots & \vdots \\
     0       &   \cdots   &  k_11  & k_12       & \cdots   &     0   \\
     0       &   \cdots   & k_21  & k_22        & \cdots   &    0    \\
\vdots & \ddots    &\vdots &   \vdots    & \ddots & \vdots \\
  0         &    \cdots  &      0      &       0           &  \cdots  &    0
\end{bmatrix}
\begin{Bmatrix}
0 \\
\vdots  \\
u_200 \\
v_200\\
\vdots \\
0\\
\end{Bmatrix}
+\begin{bmatrix}
     0       & \cdots     &    0        &        0       & \cdots  &       0   \\
\vdots & \ddots    & \vdots &   \vdots   & \ddots & \vdots \\
     0       &   \cdots   &  k_13  & k_14       & \cdots   &     0   \\
     0       &   \cdots   & k_23  & k_24        & \cdots   &    0    \\
\vdots & \ddots    &\vdots &   \vdots    & \ddots & \vdots \\
  0         &    \cdots  &      0      &       0           &  \cdots  &    0
\end{bmatrix}
\begin{Bmatrix}
0 \\
\vdots  \\
u_204 \\
v_204\\
\vdots \\
0\\
\end{Bmatrix}
+\begin{bmatrix}
     0       & \cdots     &    0        &        0       & \cdots  &       0   \\
\vdots & \ddots    & \vdots &   \vdots   & \ddots & \vdots \\
     0       &   \cdots   &  k_15  & k_16       & \cdots   &     0   \\
     0       &   \cdots   & k_25  & k_26        & \cdots   &    0    \\
\vdots & \ddots    &\vdots &   \vdots    & \ddots & \vdots \\
  0         &    \cdots  &      0      &       0           &  \cdots  &    0
\end{bmatrix}
\begin{Bmatrix}
0 \\
\vdots  \\
u_205 \\
v_205\\
\vdots \\
0\\
\end{Bmatrix}
=\begin{Bmatrix} 0 \\ \vdots \\ F_{x200} \\  F_{y200} \\  \vdots \\ 0  \end{Bmatrix}
\end{equation}](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A%5Cbegin%7Bbmatrix%7D%0A+++++0+++++++%26+%5Ccdots+++++%26++++0++++++++%26++++++++0+++++++%26+%5Ccdots++%26+++++++0+++%5C%5C%0A%5Cvdots+%26+%5Cddots++++%26+%5Cvdots+%26+++%5Cvdots+++%26+%5Cddots+%26+%5Cvdots+%5C%5C%0A+++++0+++++++%26+++%5Ccdots+++%26++k_11++%26+k_12+++++++%26+%5Ccdots+++%26+++++0+++%5C%5C%0A+++++0+++++++%26+++%5Ccdots+++%26+k_21++%26+k_22++++++++%26+%5Ccdots+++%26++++0++++%5C%5C%0A%5Cvdots+%26+%5Cddots++++%26%5Cvdots+%26+++%5Cvdots++++%26+%5Cddots+%26+%5Cvdots+%5C%5C%0A++0+++++++++%26++++%5Ccdots++%26++++++0++++++%26+++++++0+++++++++++%26++%5Ccdots++%26++++0%0A%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D%0A0+%5C%5C%0A%5Cvdots++%5C%5C%0Au_200+%5C%5C%0Av_200%5C%5C%0A%5Cvdots+%5C%5C%0A0%5C%5C%0A%5Cend%7BBmatrix%7D%0A%2B%5Cbegin%7Bbmatrix%7D%0A+++++0+++++++%26+%5Ccdots+++++%26++++0++++++++%26++++++++0+++++++%26+%5Ccdots++%26+++++++0+++%5C%5C%0A%5Cvdots+%26+%5Cddots++++%26+%5Cvdots+%26+++%5Cvdots+++%26+%5Cddots+%26+%5Cvdots+%5C%5C%0A+++++0+++++++%26+++%5Ccdots+++%26++k_13++%26+k_14+++++++%26+%5Ccdots+++%26+++++0+++%5C%5C%0A+++++0+++++++%26+++%5Ccdots+++%26+k_23++%26+k_24++++++++%26+%5Ccdots+++%26++++0++++%5C%5C%0A%5Cvdots+%26+%5Cddots++++%26%5Cvdots+%26+++%5Cvdots++++%26+%5Cddots+%26+%5Cvdots+%5C%5C%0A++0+++++++++%26++++%5Ccdots++%26++++++0++++++%26+++++++0+++++++++++%26++%5Ccdots++%26++++0%0A%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D%0A0+%5C%5C%0A%5Cvdots++%5C%5C%0Au_204+%5C%5C%0Av_204%5C%5C%0A%5Cvdots+%5C%5C%0A0%5C%5C%0A%5Cend%7BBmatrix%7D%0A%2B%5Cbegin%7Bbmatrix%7D%0A+++++0+++++++%26+%5Ccdots+++++%26++++0++++++++%26++++++++0+++++++%26+%5Ccdots++%26+++++++0+++%5C%5C%0A%5Cvdots+%26+%5Cddots++++%26+%5Cvdots+%26+++%5Cvdots+++%26+%5Cddots+%26+%5Cvdots+%5C%5C%0A+++++0+++++++%26+++%5Ccdots+++%26++k_15++%26+k_16+++++++%26+%5Ccdots+++%26+++++0+++%5C%5C%0A+++++0+++++++%26+++%5Ccdots+++%26+k_25++%26+k_26++++++++%26+%5Ccdots+++%26++++0++++%5C%5C%0A%5Cvdots+%26+%5Cddots++++%26%5Cvdots+%26+++%5Cvdots++++%26+%5Cddots+%26+%5Cvdots+%5C%5C%0A++0+++++++++%26++++%5Ccdots++%26++++++0++++++%26+++++++0+++++++++++%26++%5Ccdots++%26++++0%0A%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D%0A0+%5C%5C%0A%5Cvdots++%5C%5C%0Au_205+%5C%5C%0Av_205%5C%5C%0A%5Cvdots+%5C%5C%0A0%5C%5C%0A%5Cend%7BBmatrix%7D%0A%3D%5Cbegin%7BBmatrix%7D+0+%5C%5C+%5Cvdots+%5C%5C+F_%7Bx200%7D+%5C%5C++F_%7By200%7D+%5C%5C++%5Cvdots+%5C%5C+0++%5Cend%7BBmatrix%7D%0A%5Cend%7Bequation%7D)

これらの式がほかの要素でも成り立ち、重複する節点の要素については和をとればよい。
このようにして全体剛性マトリクスに入れていく。


### プログラム解説

あるエレメント`i`に対して、順番に全体剛性マトリクスに代入していく。
エレメントごとに作成される要素剛性マトリクスKeの

j番目に対応する`pt1節点`の荷重、k番目に対応する`pt2節点`の変位の関係を表す`2j`行,`2k`列を左上とした2x2の行列が、
全体の`pt1`行`pt2`列に対応した部分に入る。（2倍したり-1したり色々する。）


なお、Kmatは祖行列であり、以下の黒い部分のみが非0である。

![image](https://user-images.githubusercontent.com/88224293/166095413-2be7a0fa-f4ab-4383-bfec-a7d4b9c3cf34.png)

今回は普通の行列として扱っている。



## makeFmat

節点荷重ベクトルを作成する。
今回、荷重が与えられている節点について、`force_pnt`に接点番号、向き(x:1, y:2)が、大きさがforceに同じ順で格納されている。
なお、入力で荷重が指定されていない節点に関しては、すべて0が与えられていると考えており、
そのうち変位が与えられた接点に関しては後から求めて上書きしている。

### プログラム解説
x:1、y:2ということと、行列でxy交互に並んでいることからうまく計算して場所を指定している。



## makeUmat

節点変位ベクトルを作成する。
作り方は`Fmat`と全く同じ

なお、与えられていない部分はすべて0で初期化されているが、後から求めて上書きしている。


## makeSUBmatrix

K、U、Fを並べ替えて未知成分、既知成分に分けたブロック行列を作成する。

![\begin{equation}
\begin{bmatrix}
K_11 & K_12  \\
K_21 & K_22 
\end{bmatrix}
\begin{Bmatrix} d_{1unknown} \\ d_{2known} \end{Bmatrix}
=\begin{Bmatrix} F_{1known} \\  F_{2unknown} \end{Bmatrix}
\end{equation}](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A%5Cbegin%7Bbmatrix%7D%0AK_11+%26+K_12++%5C%5C%0AK_21+%26+K_22+%0A%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D+d_%7B1unknown%7D+%5C%5C+d_%7B2known%7D+%5Cend%7BBmatrix%7D%0A%3D%5Cbegin%7BBmatrix%7D+F_%7B1known%7D+%5C%5C++F_%7B2unknown%7D+%5Cend%7BBmatrix%7D%0A%5Cend%7Bequation%7D)

勉強中


##  makeInverse

K11の逆行列を計算
オリジナルではガウスの消去法を使用しているが、Pythonではライブラリを使用して1行で終了




##  solveUmat

節点変位ベクトルを求める。

![\begin{equation}
\boldsymbol{d_{1unknown}}=\boldsymbol{K_11}^{-1}(\boldsymbol{F_{1known}} - \boldsymbol{K_12}\boldsymbol{d_{2known}})
\end{equation}](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A%5Cboldsymbol%7Bd_%7B1unknown%7D%7D%3D%5Cboldsymbol%7BK_11%7D%5E%7B-1%7D%28%5Cboldsymbol%7BF_%7B1known%7D%7D+-+%5Cboldsymbol%7BK_12%7D%5Cboldsymbol%7Bd_%7B2known%7D%7D%29%0A%5Cend%7Bequation%7D)

その後元の`Umat`に代入しなおす。



## solveFmat

節点荷重ベクトルを求める。

![\begin{equation}
\boldsymbol{F_{2unknown}}=\boldsymbol{K_21}\boldsymbol{d_{1nowknown}} +\boldsymbol{K_22}\boldsymbol{d_{2known}} 
\end{equation}](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A%5Cboldsymbol%7BF_%7B2unknown%7D%7D%3D%5Cboldsymbol%7BK_21%7D%5Cboldsymbol%7Bd_%7B1nowknown%7D%7D+%2B%5Cboldsymbol%7BK_22%7D%5Cboldsymbol%7Bd_%7B2known%7D%7D+%0A%5Cend%7Bequation%7D)

その後元の`Fmat`に代入しなおす。




## displacement


見やすいように`amp`倍した**節点** の変位後の位置を出力





## distribution

各**要素** のひずみ`strain`、荷重`stress`を求める。


ひずみ

![\begin{equation}
\boldsymbol{\epsilon}=
\begin{Bmatrix}
\cfrac{\partial u}{\partial x} \\
\cfrac{\partial v}{\partial y} \\
\cfrac{\partial u}{\partial y}+\cfrac{\partial v}{\partial x}
\end{Bmatrix}
=\begin{bmatrix}
\cfrac{\partial N_i}{\partial x} & 0 & \cfrac{\partial N_j}{\partial x} & 0 & \cfrac{\partial N_k}{\partial x} & 0 \\
0 & \cfrac{\partial N_i}{\partial y} & 0 & \cfrac{\partial N_j}{\partial y} & 0 & \cfrac{\partial N_k}{\partial y} \\
\cfrac{\partial N_i}{\partial y} & \cfrac{\partial N_i}{\partial x} &
\cfrac{\partial N_j}{\partial y} & \cfrac{\partial N_j}{\partial x} &
\cfrac{\partial N_k}{\partial y} & \cfrac{\partial N_k}{\partial x}
\end{bmatrix}
\begin{Bmatrix} u_1 \\ v_1 \\ u_2\\ v_2 \\u_3 \\v_3 \end{Bmatrix}
=[\boldsymbol{B_e}]\{\boldsymbol{d_e}\}
\end{equation}](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A%5Cboldsymbol%7B%5Cepsilon%7D%3D%0A%5Cbegin%7BBmatrix%7D%0A%5Ccfrac%7B%5Cpartial+u%7D%7B%5Cpartial+x%7D+%5C%5C%0A%5Ccfrac%7B%5Cpartial+v%7D%7B%5Cpartial+y%7D+%5C%5C%0A%5Ccfrac%7B%5Cpartial+u%7D%7B%5Cpartial+y%7D%2B%5Ccfrac%7B%5Cpartial+v%7D%7B%5Cpartial+x%7D%0A%5Cend%7BBmatrix%7D%0A%3D%5Cbegin%7Bbmatrix%7D%0A%5Ccfrac%7B%5Cpartial+N_i%7D%7B%5Cpartial+x%7D+%26+0+%26+%5Ccfrac%7B%5Cpartial+N_j%7D%7B%5Cpartial+x%7D+%26+0+%26+%5Ccfrac%7B%5Cpartial+N_k%7D%7B%5Cpartial+x%7D+%26+0+%5C%5C%0A0+%26+%5Ccfrac%7B%5Cpartial+N_i%7D%7B%5Cpartial+y%7D+%26+0+%26+%5Ccfrac%7B%5Cpartial+N_j%7D%7B%5Cpartial+y%7D+%26+0+%26+%5Ccfrac%7B%5Cpartial+N_k%7D%7B%5Cpartial+y%7D+%5C%5C%0A%5Ccfrac%7B%5Cpartial+N_i%7D%7B%5Cpartial+y%7D+%26+%5Ccfrac%7B%5Cpartial+N_i%7D%7B%5Cpartial+x%7D+%26%0A%5Ccfrac%7B%5Cpartial+N_j%7D%7B%5Cpartial+y%7D+%26+%5Ccfrac%7B%5Cpartial+N_j%7D%7B%5Cpartial+x%7D+%26%0A%5Ccfrac%7B%5Cpartial+N_k%7D%7B%5Cpartial+y%7D+%26+%5Ccfrac%7B%5Cpartial+N_k%7D%7B%5Cpartial+x%7D%0A%5Cend%7Bbmatrix%7D%0A%5Cbegin%7BBmatrix%7D+u_1+%5C%5C+v_1+%5C%5C+u_2%5C%5C+v_2+%5C%5Cu_3+%5C%5Cv_3+%5Cend%7BBmatrix%7D%0A%3D%5B%5Cboldsymbol%7BB_e%7D%5D%5C%7B%5Cboldsymbol%7Bd_e%7D%5C%7D%0A%5Cend%7Bequation%7D)


応力


![\begin{equation}
 \sigma = D \epsilon
\end{equation}
](https://render.githubusercontent.com/render/math?math=%5Ccolor%7Bblack%7D%5Clarge+%5Cdisplaystyle+%5Cbegin%7Bequation%7D%0A+%5Csigma+%3D+D+%5Cepsilon%0A%5Cend%7Bequation%7D%0A)



## メッシュの可視化

https://qiita.com/itotomball/items/e63039d186fa1f564513







