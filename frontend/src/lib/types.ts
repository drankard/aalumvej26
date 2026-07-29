/** One row of a facts table. Either sourced from a crawled page or site-computed. */
export interface Fact {
  label: string;
  value: string;
  source_url?: string | null;
  computed?: boolean;
}

export interface FaqItem {
  question: string;
  answer: string;
}

export interface PostTranslation {
  title: string;
  excerpt: string;
  date: string;
  /** Depth fields — absent on posts written before the content expansion. */
  tldr?: string;
  body?: string;
  facts?: Fact[];
  faq?: FaqItem[];
  from_house?: string;
}

export interface Post {
  id: string;
  category: string;
  tag_key: string;
  url: string;
  emoji: string;
  sort_order: number;
  status: string;
  relevance_score: number;
  source_urls: string[];
  event_start?: string | null;
  event_end?: string | null;
  translations: Record<string, PostTranslation>;
  created_at: string;
  updated_at: string;
}

export interface AreaTranslation {
  name: string;
  dist: string;
  desc: string;
  body?: string;
  facts?: Fact[];
  faq?: FaqItem[];
  from_house?: string;
}

export interface Area {
  id: string;
  url: string;
  sort_order: number;
  status: string;
  translations: Record<string, AreaTranslation>;
  created_at: string;
  updated_at: string;
}

export interface CategoryTranslation {
  label: string;
}

export interface Category {
  id: string;
  icon: string;
  sort_order: number;
  translations: Record<string, CategoryTranslation>;
  created_at: string;
  updated_at: string;
}

export interface SiteContent {
  posts: Post[];
  areas: Area[];
  categories: Category[];
  archivedPosts: Post[];
  postSlugs: Map<string, string>;
  areaSlugs: Map<string, string>;
}
