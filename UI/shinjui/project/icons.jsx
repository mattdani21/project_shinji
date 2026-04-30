// Tiny stroke-based iOS-flavored icons. 1.5px strokes, square caps rounded.
const Icon = ({ d, size = 16, stroke = 1.6, fill = "none", className, style }) => (
  <svg
    width={size} height={size} viewBox="0 0 24 24"
    fill={fill} stroke="currentColor" strokeWidth={stroke}
    strokeLinecap="round" strokeLinejoin="round"
    className={className} style={style} aria-hidden="true"
  >{d}</svg>
);

const I = {
  Inbox: (p) => <Icon {...p} d={<>
    <path d="M3 13l3-7h12l3 7" />
    <path d="M3 13v5a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-5" />
    <path d="M3 13h5l1.5 2h5L16 13h5" />
  </>} />,
  Layers: (p) => <Icon {...p} d={<>
    <path d="M12 3l9 5-9 5-9-5 9-5z" />
    <path d="M3 13l9 5 9-5" />
    <path d="M3 17l9 5 9-5" />
  </>} />,
  Doc: (p) => <Icon {...p} d={<>
    <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
    <path d="M14 3v5h5" />
    <path d="M9 13h6M9 17h4" />
  </>} />,
  Search: (p) => <Icon {...p} d={<>
    <circle cx="11" cy="11" r="6.5" />
    <path d="M20 20l-3.5-3.5" />
  </>} />,
  Chevron: (p) => <Icon {...p} d={<path d="M9 6l6 6-6 6" />} />,
  ChevronDown: (p) => <Icon {...p} d={<path d="M6 9l6 6 6-6" />} />,
  ChevronRight: (p) => <Icon {...p} d={<path d="M9 6l6 6-6 6" />} />,
  Paperclip: (p) => <Icon {...p} d={<path d="M21 12.5L12.5 21a5.5 5.5 0 0 1-7.8-7.8l9-9a3.7 3.7 0 0 1 5.2 5.2l-9 9a1.9 1.9 0 1 1-2.6-2.6l8-8" />} />,
  Sparkle: (p) => <Icon {...p} d={<>
    <path d="M12 4l1.6 4.4L18 10l-4.4 1.6L12 16l-1.6-4.4L6 10l4.4-1.6L12 4z" />
    <path d="M19 16l.7 1.8L21.5 18.5l-1.8.7L19 21l-.7-1.8-1.8-.7 1.8-.7L19 16z" />
  </>} />,
  Check: (p) => <Icon {...p} d={<path d="M5 12l5 5L20 7" />} />,
  Dot: (p) => <Icon {...p} d={<circle cx="12" cy="12" r="3" fill="currentColor" stroke="none" />} />,
  Flag: (p) => <Icon {...p} d={<>
    <path d="M5 21V4" />
    <path d="M5 4h12l-2 4 2 4H5" />
  </>} />,
  Eye: (p) => <Icon {...p} d={<>
    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
    <circle cx="12" cy="12" r="3" />
  </>} />,
  ArrowRight: (p) => <Icon {...p} d={<>
    <path d="M5 12h14" />
    <path d="M13 6l6 6-6 6" />
  </>} />,
  Bolt: (p) => <Icon {...p} d={<path d="M13 3L4 14h7l-1 7 9-11h-7l1-7z" />} />,
  Shield: (p) => <Icon {...p} d={<>
    <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z" />
    <path d="M9 12l2 2 4-4" />
  </>} />,
};
window.I = I;
