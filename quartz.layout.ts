import { PageLayout, SharedLayout } from "./quartz/cfg"
import * as Component from "./quartz/components"

// components shared across all pages
export const sharedPageComponents: SharedLayout = {
  head: Component.Head(),
  header: [],
  afterBody: [],
  footer: Component.Footer({
    links: {
      "Built with Quartz": "https://quartz.jzhao.xyz",
    },
  }),
}

// components for pages that display a single page (e.g. a single note)
export const defaultContentPageLayout: PageLayout = {
  beforeBody: [
    Component.ConditionalRender({
      component: Component.Breadcrumbs(),
      condition: (page) => page.fileData.slug !== "index",
    }),
    Component.ArticleTitle(),
    Component.ContentMeta(),
    Component.TagList(),
  ],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Flex({
      components: [
        {
          Component: Component.Search(),
          grow: true,
        },
        { Component: Component.Darkmode() },
        { Component: Component.ReaderMode() },
      ],
    }),
    Component.Explorer({
      // sections ("1 Project", ...) in numeric order, then within a folder the hub
      // note first and the rest alphabetically
      sortFn: (a, b) => {
        const hubs = ["adlab-data-analysis", "adlab-model-fitting", "adlab-parameter-recovery"]
        if (a.isFolder && b.isFolder) {
          return a.slugSegment.localeCompare(b.slugSegment, undefined, { numeric: true })
        }
        if (a.isFolder !== b.isFolder) {
          return a.isFolder ? -1 : 1
        }
        const ha = hubs.includes(a.slugSegment)
        const hb = hubs.includes(b.slugSegment)
        if (ha !== hb) {
          return ha ? -1 : 1
        }
        return a.displayName.localeCompare(b.displayName, undefined, {
          numeric: true,
          sensitivity: "base",
        })
      },
    }),
  ],
  right: [
    Component.Graph(),
    Component.DesktopOnly(Component.TableOfContents()),
    Component.Backlinks(),
  ],
}

// components for pages that display lists of pages  (e.g. tags or folders)
export const defaultListPageLayout: PageLayout = {
  beforeBody: [Component.Breadcrumbs(), Component.ArticleTitle(), Component.ContentMeta()],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Flex({
      components: [
        {
          Component: Component.Search(),
          grow: true,
        },
        { Component: Component.Darkmode() },
      ],
    }),
    Component.Explorer({
      // sections ("1 Project", ...) in numeric order, then within a folder the hub
      // note first and the rest alphabetically
      sortFn: (a, b) => {
        const hubs = ["adlab-data-analysis", "adlab-model-fitting", "adlab-parameter-recovery"]
        if (a.isFolder && b.isFolder) {
          return a.slugSegment.localeCompare(b.slugSegment, undefined, { numeric: true })
        }
        if (a.isFolder !== b.isFolder) {
          return a.isFolder ? -1 : 1
        }
        const ha = hubs.includes(a.slugSegment)
        const hb = hubs.includes(b.slugSegment)
        if (ha !== hb) {
          return ha ? -1 : 1
        }
        return a.displayName.localeCompare(b.displayName, undefined, {
          numeric: true,
          sensitivity: "base",
        })
      },
    }),
  ],
  right: [],
}
