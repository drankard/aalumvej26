export const SITE = "https://www.aalumvej26.dk";

// The house's name as it is written for humans and for structured data.
//
// Deliberately distinct from the domain: the domain is an ASCII identifier and
// cannot carry the Å, but the address genuinely is "Ålumvej 26" and that is what
// maps, tourism sites and directories match on. The site previously used both
// spellings — including two different `name` values on schema.org nodes sharing
// one @id, which declares a single entity under two names. One constant so that
// cannot recur.
export const HOUSE_NAME = "Ålumvej 26";

export const BOOKING =
  "https://www.aggerferiehuse.dk/dk/agger/lille-feriehus-med-sjael-og-charme";

export const META_PIXEL_ID = "1655071254807080";

export const TAG_COLORS: Record<string, string> = {
  event: "#B8624C",
  guide: "#7A8B5C",
  openNow: "#4A9B7F",
  seasonBest: "#8B7355",
  activity: "#5A7A8A",
  kidFriendly: "#C4944A",
  localFavorite: "#8B7355",
  culturalHistory: "#3D4F5F",
  natureGem: "#7A8B5C",
  bigEvent: "#B8624C",
};

// House photography.
//
// These are imported rather than referenced by public/ path so the build runs
// them through astro:assets: responsive widths, WebP, and real intrinsic
// dimensions on every <img>. Straight-from-public/ <img> tags shipped the full
// 4032x3024 master to every visitor and declared no dimensions at all.
//
// Masters live in src/assets/house/ capped at 2400px wide — see
// scripts/downscale-masters.mjs for why and how to re-apply after adding one.
import exterior from "../assets/house/01-exterior.jpg";
import exterior2 from "../assets/house/02-exterior2.jpg";
import kitchen1 from "../assets/house/03-kitchen1.jpg";
import kitchen2 from "../assets/house/04-kitchen2.jpg";
import house3 from "../assets/house/05-house3.jpg";
import house4 from "../assets/house/06-house4.jpg";
import livingroom1 from "../assets/house/07-livingroom1.jpg";
import livingroom2 from "../assets/house/08-livingroom2.jpg";
import bedroom1 from "../assets/house/10-bedroom1.jpg";
import house5 from "../assets/house/11-house5.jpg";
import bedroom2 from "../assets/house/12-bedroom2.jpg";
import bathroom from "../assets/house/13-bathroom.jpg";
import house6 from "../assets/house/14-house6.jpg";
import house7 from "../assets/house/15-house7.jpg";
import house8 from "../assets/house/16-house8.jpg";

export interface HouseImage {
  img: ImageMetadata;
  alt: string;
}

export const HOUSE_IMAGES: HouseImage[] = [
  { img: exterior, alt: "Stråtækt feriehus set udefra, Ålumvej 26 i Agger" },
  { img: livingroom1, alt: "Hyggelig stue med brændeovn i feriehuset" },
  { img: livingroom2, alt: "Lys stue med udsigt til naturen" },
  { img: kitchen1, alt: "Fuldt udstyret køkken med spiseplads" },
  { img: kitchen2, alt: "Køkken med moderne faciliteter" },
  { img: bedroom1, alt: "Soveværelse med dobbeltseng" },
  { img: bedroom2, alt: "Ekstra soveværelse i feriehuset" },
  { img: bathroom, alt: "Badeværelse med brusekabine" },
  { img: exterior2, alt: "Feriehuset set fra haven med stor naturgrund" },
  { img: house3, alt: "Stråtag og træfacade i naturlige omgivelser" },
  { img: house4, alt: "Indgangsparti med charme og karakter" },
  { img: house5, alt: "Interiør detalje fra det renoverede feriehus" },
  { img: house6, alt: "Udeområde med terrasse og grønt" },
  { img: house7, alt: "Naturgrund med klitlandskab tæt på havet" },
  { img: house8, alt: "Aftenstemning ved feriehuset i Agger" },
];

/** The image every page falls back to for og:image. */
export const OG_SOURCE = exterior;
