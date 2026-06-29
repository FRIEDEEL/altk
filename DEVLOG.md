# Development log for ALTK
Integrate future plan and notes during developing.


## Dated notes
### 260629-042459
ScmagData quantity design notes:
- Public data access should be quantity-oriented rather than dataframe-column-oriented.
  `COL_*` constants are still useful as internal/materialized column names, but user-facing
  analysis APIs should prefer quantity names such as `T`, `I`, `Q`, `P`, `J`, `beta`,
  `I_beta`, and `J_beta`.
- Quantities that are uniquely determined by one measurement can be exposed as properties.
  Examples: `P = Q / area`, `J = I / area`, `beta = dT / dt`, `I_beta = I / beta`,
  and `J_beta = J / beta`. These may be computed on access or read from materialized
  columns if a processed dataset already stores them.
- Transformations that depend on external choices should return new `ScmagData` objects
  rather than mutate the original data. Examples include interpolation, alignment, cropping,
  smoothing with chosen parameters, and background subtraction.
- Alignment is a multi-dataset operation, so it is better represented as a module-level
  function than as a method of one `ScmagData`. The current `align_on()` API aligns several
  datasets on a shared quantity grid from a reference dataset and clips the grid to the
  common covered range.
- Interpolation/alignment should resolve quantities through `ScmagData` properties, not
  assume that every requested quantity exists as a raw dataframe column. This avoids the
  ambiguity between raw columns and derived quantities such as `I_beta`.
- Processed/aligned results can still be represented as `ScmagData` to preserve the idea
  that `T`, `I`, `Q`, and derived quantities belong to the same measurement-derived data
  object. Materialized derived columns should have distinct column names to avoid confusing
  raw quantities (`Q`, `I`) with derived quantities (`P`, `J`).

### 260625-050909
TODOs for scmag:
- generalize the interpolate API

### 260526-032559
Add dataclass to structured data, in order to have easier access to the data, as well as containing the metadata within the structured data.

### 260523-052804
Typing(customized types) should be settled in a submodule typing. (maybe)

### 260523-051031
Refactoring:

contain the standard flow to workflows.
the rest of the package is "the reused tools in building the workflows."

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
