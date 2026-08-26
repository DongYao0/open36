const modules = import.meta.glob('../assets/contests/competition-art/*', { eager: true, import: 'default' })

export const contestArt = Object.fromEntries(
  Object.entries(modules).map(([path, source]) => [path.split('/').pop().replace(/\.[^.]+$/, ''), source])
)

export const getContestArt = id => contestArt[id]
