// {% raw %}
#import "@preview/lovelace:0.3.0": pseudocode-list
#set page(paper: "us-letter", margin: 1cm)
#set text(size: 12pt)
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => {
  set align(center)
  set text(size: 16pt)
  it
}
#show heading.where(level: 2): it => {
  set align(center)
  set text(size: 14pt)
  it
}
#show heading.where(level: 3): it => {
  set align(center)
  set text(size: 12pt, fill: blue)
  it
}


#heading(level: 1, numbering: none)[6.1400 PS01]
#align(center)[
  Gatlen Culp (gculp\@mit.edu)
  #sym.dot 2025-05-21 \
  Collaborators: None #sym.dot Resources Used: None
]

#columns(2)[
  = Regular Languages

  Closure under:
  $
    A union B, quad A sect B, quad A^R, quad A^*, quad not A, \
    A dot B, quad A - B = A sect (not B)
  $
]


// Alternative.
// #import "../preamble.typ": *

// #show: homework.with(
//   title: "PS01",
//   date: datetime(year: 2026, month: 2, day: 18),
// )

// #show: style.with()

// #set heading(numbering: "1.1")

// = Probability Review

// #question(status: "todo")[
//   Please use the accompanying bubble sheet for submitting your solutions for this problem.

//   In what follows, $Phi$ is the CDF of the standard Gaussian (Normal) distribution.

//   Let $X$ be a random variable taking values between $0$ and $pi$, with pdf given by
//   $
//     f(x) = c sin x, quad x in [0, pi].
//   $

//   1. What is the value of $c$? #h(1em) (a) $pi$ #h(1em) (b) $1\/2$ #h(1em) (c) $2$ #h(1em) (d) $1\/pi$

//   2. What is $EE[X]$? #h(1em) (a) $pi\/2$ #h(1em) (b) $pi$ #h(1em) (c) $1$ #h(1em) (d) $1\/2$
// ]

// #solution[
// ]

// #pagebreak()

// = Convergence of Uniforms

// #question(status: "todo")[
//   Let $X_n tilde "Unif"(-1\/n, 1\/n)$ and let $X$ be a random variable such that $PP(X = 0) = 1$.

//   + Compute and draw the CDF $F_n (x)$ and $F(x)$ of $X_n$ and $X$ respectively.

//   + Does $X_n arrow.r^P X$? (prove or disprove)

//   + Does $X_n arrow.squiggly X$? (prove or disprove)
// ]

// #pagebreak()


// {% endraw %}
