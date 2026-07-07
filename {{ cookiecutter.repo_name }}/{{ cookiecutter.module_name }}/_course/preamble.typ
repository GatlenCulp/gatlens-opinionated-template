#import "@local/gat-typst:0.1.0": *

// Overwrites for class
#let personal-info = (
  university: "MIT",
  author: "Gatlen Culp",
  email: "gculp@mit.edu",
  collaborators: [Claude 4.6 Sonnet (Questions, not Solving)],
  resources: [None],
)

#let course-info = (
  course: link("https://web.mit.edu/6.7920/www/schedule.html")[18.650 Stats],
)

#let info = personal-info + course-info

#let homework = homework.with(
  ..info,
)
#let cheatsheet = cheatsheet.with(
  ..info,
)
