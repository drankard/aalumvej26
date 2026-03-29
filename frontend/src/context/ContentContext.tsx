import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";
import { rpc } from "../api/client";

export interface PostTranslation {
  title: string;
  excerpt: string;
  date: string;
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
  translations: Record<string, PostTranslation>;
  created_at: string;
  updated_at: string;
}

export interface AreaTranslation {
  name: string;
  dist: string;
  desc: string;
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

interface ContentData {
  posts: Post[];
  areas: Area[];
  categories: Category[];
}

interface ContentState {
  posts: Post[];
  areas: Area[];
  categories: Category[];
  archivedPosts: Post[];
  loading: boolean;
  error: string | null;
  loadArchive: () => void;
}

const ContentContext = createContext<ContentState>({
  posts: [],
  areas: [],
  categories: [],
  archivedPosts: [],
  loading: true,
  error: null,
  loadArchive: () => {},
});

export function ContentProvider({ children }: { children: ReactNode }) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [areas, setAreas] = useState<Area[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [archivedPosts, setArchivedPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    rpc<ContentData>("list_content")
      .then((data) => {
        setPosts(data.posts);
        setAreas(data.areas);
        setCategories(data.categories);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const loadArchive = useCallback(() => {
    if (archivedPosts.length > 0) return;
    rpc<Post[]>("list_archived_posts")
      .then(setArchivedPosts)
      .catch(() => {});
  }, [archivedPosts.length]);

  return (
    <ContentContext.Provider value={{ posts, areas, categories, archivedPosts, loading, error, loadArchive }}>
      {children}
    </ContentContext.Provider>
  );
}

export function useContent() {
  return useContext(ContentContext);
}
