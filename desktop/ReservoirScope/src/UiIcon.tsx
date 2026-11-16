type IconName = 'folder' | 'refresh' | 'play' | 'pause' | 'stop' | 'menu' | 'close' | 'previous' | 'next';
const paths: Record<IconName, string> = {
  folder: 'M3 7V4h6l2 2h8v3 M2 9h7l2 2h11l-3 9H2z',
  refresh: 'M20 10a8 8 0 1 0-2 8 M20 3v7h-7',
  play: 'M7 4l14 8-14 8z',
  pause: 'M8 5v14 M16 5v14',
  stop: 'M6 6h12v12H6z',
  menu: 'M4 6h16 M4 12h16 M4 18h16',
  close: 'M6 6l12 12 M18 6L6 18',
  previous: 'M15 5l-7 7 7 7',
  next: 'M9 5l7 7-7 7',
};
export default function UiIcon({ name }: { name: IconName }) {
  return <svg className="ui-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false"><path d={paths[name]}/></svg>;
}
