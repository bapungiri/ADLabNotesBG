// Click any figure in a note to see it full size (overlay); click again or press Esc to close.
// @ts-ignore
import imageZoomScript from "./scripts/imagezoom.inline"
import styles from "./styles/imagezoom.scss"
import { QuartzComponent, QuartzComponentConstructor } from "./types"

const ImageZoom: QuartzComponent = () => null

ImageZoom.afterDOMLoaded = imageZoomScript
ImageZoom.css = styles

export default (() => ImageZoom) satisfies QuartzComponentConstructor
