# Development log for ALTK
Integrate future plan and notes during developing.


## Dated notes

### 251227-143307
The common data form should be numpy Ndarray.

Easy to process, abundant API for multiple data processing.

On a second thought, pandas is good.


### 260116-150708
#### About Derivative

If we have a data sequence
$$
\{ X_i, Y_i \}
$$

Then for a data point, say, $X_p$.
The $n$th order polynomial expansion form is 
$$
y(x) = Y_p+\sum_{k=1}^n a_k(x-X_p)^k
$$

Take $2m+1$ data points with $Y_p$ at center for fitting, then the variance is
$$
\sigma^2 = \sum_{l=-m}^m(y(X_{p+l})-Y_{p+l})^2
$$

Derivative to parameters $a_i$
$$
\begin{align*}
{\partial \sigma^2\over \partial a_i} =&
\sum_{l=-m}^m2(y(X_{p+l})-Y_{p+l})
\cdot {\partial y(X_{p+l})\over \partial a_i}\\
=&2\sum_{l=-m}^m (y(X_{p+l})-Y_{p+l})
\cdot (X_{p+l}-X_p)^i\\
=&2\sum_{l=-m}^m
(
    Y_p+\sum_{j=1}^n 
    a_j(X_{p+l}-X_p)^j
    -Y_{p+l}
)
\cdot (X_{p+l}-X_p)^i\\
=&
\Big(
    2
    \sum_{j=1}^n a_j
    \big(
        \sum_{l=-m}^{m}(X_{p+l}-X_p)^{j+i}
    \big)
\Big)+
\Big(2
    \sum_{l=-m}^m(Y_p-Y_{p+l})\cdot(X_{p+l}-X_p)^i
\Big)
\end{align*}
$$

To minimize $\sigma^2$,
$$
\begin{align*}
\dd \sigma^2 =& \sum_k {\partial\sigma^2\over \partial a_k}\dd a_k\\ = 0
\end{align*}
$$
To make the system of equations consistent, a choice should be $n = 2m+1$.
Therefore, system of equations can be written as 
$$
\begin{align*}
\sum_{j}A_{ij} a_j = b_i
\end{align*}
$$
With
$$
\begin{align*}
A_{ij} =&
\sum_{l=-m}^{m}(X_{p+l}-X_p)^{j+i} \\
b_i = &
\sum_{l=-m}^m(Y_{p+l}-Y_{p})\cdot(X_{p+l}-X_p)^i
\end{align*}
$$


Now let's consider the derivatives.
At $x=X_p$, the $r$th ($r=1,2,\dots$) order derivative should therefore be 
$$
\begin{align*}
{\dd ^r y\over \dd x^r}\vert_{x=X_p} =& r!a_r\\
\end{align*}
$$