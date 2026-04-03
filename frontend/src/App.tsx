import { useState, useEffect, useCallback, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useContent, Post } from "./context/ContentContext";

const C = {
  foam: "#F5F0E8", sand: "#D4C5A9", driftwood: "#8B7355",
  sea: "#5A7A8A", deep: "#2C3E50", rust: "#B8624C",
  storm: "#3D4F5F", marram: "#7A8B5C", cloud: "#E8E2D6",
};

const BOOKING = "https://www.aggerferiehuse.dk/dk/agger/lille-feriehus-med-sjael-og-charme";

declare global { interface Window { fbq?: (...args: unknown[]) => void; } }
const trackContact = () => window.fbq?.("track", "Contact");


const TAG_COLORS: Record<string, string> = {
  event: C.rust, guide: C.marram, openNow: "#4A9B7F", seasonBest: C.driftwood,
  activity: C.sea, kidFriendly: "#C4944A", localFavorite: C.driftwood,
  culturalHistory: C.storm, natureGem: C.marram, bigEvent: C.rust,
};

const LANGS = [
  { code: "da", label: "DA" },
  { code: "en", label: "EN" },
  { code: "de", label: "DE" },
];

function Card({ item, idx }: { item: Post; idx: number }) {
  const { t, i18n } = useTranslation();
  const [h, setH] = useState(false);
  const bg = TAG_COLORS[item.tag_key] || C.sea;
  const tag = t(`tags.${item.tag_key}`);
  const tr = item.translations[i18n.language] ?? item.translations["da"];
  const title = tr?.title ?? "";
  const excerpt = tr?.excerpt ?? "";
  const date = tr?.date ?? "";

  return (
    <a href={item.url} target="_blank" rel="noopener noreferrer"
      onMouseEnter={() => setH(true)}
      onMouseLeave={() => setH(false)}
      style={{
        display: "block", background: "white", borderRadius: "12px", overflow: "hidden",
        textDecoration: "none", transition: "all 0.35s cubic-bezier(0.22,1,0.36,1)",
        transform: h ? "translateY(-3px)" : "none",
        boxShadow: h ? "0 16px 48px rgba(44,62,80,0.12)" : "0 2px 10px rgba(44,62,80,0.05)",
        animation: "fadeUp 0.45s ease " + (idx * 0.05) + "s both",
      }}>
      <div style={{
        height: "100px", background: "linear-gradient(135deg, " + bg + "33, " + C.deep + "22)",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: "36px", transition: "height 0.3s",
      }}>{item.emoji}</div>
      <div style={{ padding: "20px 22px 24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
          <span style={{
            background: bg, color: "white", padding: "2px 9px", borderRadius: "4px",
            fontFamily: "'DM Sans',sans-serif", fontSize: "10px", fontWeight: 700,
            letterSpacing: "0.07em", textTransform: "uppercase",
          }}>{tag}</span>
          <span style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "11px", color: C.driftwood }}>{date}</span>
        </div>
        <h3 style={{
          fontFamily: "'Playfair Display',serif", fontSize: "18px", fontWeight: 500,
          color: C.deep, margin: "0 0 8px", lineHeight: 1.3,
        }}>{title}</h3>
        <p style={{
          fontFamily: "'DM Sans',sans-serif", fontSize: "13px", color: C.storm,
          lineHeight: 1.65, margin: 0, opacity: 0.75,
        }}>{excerpt}</p>
        <div style={{
          marginTop: "14px", fontFamily: "'DM Sans',sans-serif", fontSize: "12px",
          fontWeight: 600, color: C.rust, display: "flex", alignItems: "center",
          gap: h ? "10px" : "6px", transition: "gap 0.3s",
        }}>{t("experiences.readMore")}</div>
      </div>
    </a>
  );
}

function App() {
  const { t, i18n } = useTranslation();
  const { posts, areas, categories, archivedPosts, loading, loadArchive } = useContent();
  const [sticky, setSticky] = useState(false);
  const [scr, setScr] = useState(false);
  const [active, setActive] = useState("hero");
  const [cat, setCat] = useState("all");
  const [showAll, setShowAll] = useState(false);
  const [showArchive, setShowArchive] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [hImg, setHImg] = useState(0);
  const imgPaused = useRef(false);
  const imgResumeTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const advanceImg = useCallback(() => {
    setHImg((p) => (p + 1) % 15);
    imgPaused.current = true;
    clearTimeout(imgResumeTimer.current);
    imgResumeTimer.current = setTimeout(() => { imgPaused.current = false; }, 10000);
  }, []);

  const go = useCallback(function (id: string) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  useEffect(() => { setTimeout(() => setLoaded(true), 150); }, []);
  useEffect(() => {
    const iv = setInterval(() => { if (!imgPaused.current) setHImg((p) => (p + 1) % 15); }, 5000);
    return () => clearInterval(iv);
  }, []);
  useEffect(() => {
    function onS() {
      setSticky(window.scrollY > window.innerHeight * 0.5);
      setScr(window.scrollY > 60);
      const ids = ["omraadet", "oplevelser", "huset", "hero"];
      for (let i = 0; i < ids.length; i++) {
        const el = document.getElementById(ids[i]);
        if (el && el.getBoundingClientRect().top <= 200) { setActive(ids[i]); break; }
      }
    }
    window.addEventListener("scroll", onS);
    return () => window.removeEventListener("scroll", onS);
  }, []);

  const filtered = cat === "all" ? posts : posts.filter((p) => p.category === cat);
  const displayed = showAll ? filtered : filtered.slice(0, 6);
  const navLinks = [
    { id: "huset", key: "nav.house" },
    { id: "oplevelser", key: "nav.experiences" },
    { id: "omraadet", key: "nav.area" },
  ];
  const houseImages = [
    { src: "/images/house/01-exterior.jpg", alt: "Stråtækt feriehus set udefra, Aalumvej 26 i Agger" },
    { src: "/images/house/07-livingroom1.jpg", alt: "Hyggelig stue med brændeovn i feriehuset" },
    { src: "/images/house/08-livingroom2.jpg", alt: "Lys stue med udsigt til naturen" },
    { src: "/images/house/03-kitchen1.jpg", alt: "Fuldt udstyret køkken med spiseplads" },
    { src: "/images/house/04-kitchen2.jpg", alt: "Køkken med moderne faciliteter" },
    { src: "/images/house/10-bedroom1.jpg", alt: "Soveværelse med dobbeltseng" },
    { src: "/images/house/12-bedroom2.jpg", alt: "Ekstra soveværelse i feriehuset" },
    { src: "/images/house/13-bathroom.jpg", alt: "Badeværelse med brusekabine" },
    { src: "/images/house/02-exterior2.jpg", alt: "Feriehuset set fra haven med stor naturgrund" },
    { src: "/images/house/05-house3.jpg", alt: "Stråtag og træfacade i naturlige omgivelser" },
    { src: "/images/house/06-house4.jpg", alt: "Indgangsparti med charme og karakter" },
    { src: "/images/house/11-house5.jpg", alt: "Interiør detalje fra det renoverede feriehus" },
    { src: "/images/house/14-house6.jpg", alt: "Udeområde med terrasse og grønt" },
    { src: "/images/house/15-house7.jpg", alt: "Naturgrund med klitlandskab tæt på havet" },
    { src: "/images/house/16-house8.jpg", alt: "Aftenstemning ved feriehuset i Agger" },
  ];
  const features = t("features", { returnObjects: true }) as unknown as string[];

  return (
    <div style={{ background: C.foam, minHeight: "100vh" }}>
      <style>{
        "@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap');" +
        "*{margin:0;padding:0;box-sizing:border-box}" +
        "html{scroll-behavior:smooth;scroll-padding-top:80px}" +
        "a:hover{opacity:0.88}button:hover{opacity:0.88}" +
        "::selection{background:" + C.rust + ";color:" + C.foam + "}" +
        "@keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}" +
        "@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}" +
        "@keyframes drift{0%,100%{opacity:0.3}50%{opacity:1}}"
      }</style>

      {/* NAV */}
      <nav style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 900,
        background: scr ? "rgba(44,62,80,0.93)" : "transparent",
        backdropFilter: scr ? "blur(16px)" : "none",
        borderBottom: scr ? "1px solid rgba(255,255,255,0.06)" : "none",
        transition: "all 0.4s", padding: scr ? "12px 28px" : "22px 28px",
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <button onClick={() => go("hero")} style={{
          fontFamily: "'Playfair Display',serif", fontSize: "17px", color: C.foam,
          letterSpacing: "0.08em", background: "none", border: "none", cursor: "pointer",
        }}>{t("nav.brand")}</button>
        <div style={{ display: "flex", gap: "20px", alignItems: "center" }}>
          {navLinks.map((l) => (
            <button key={l.id} onClick={() => go(l.id)} style={{
              fontFamily: "'DM Sans',sans-serif", fontSize: "11px", letterSpacing: "0.08em",
              textTransform: "uppercase", background: "none", border: "none", cursor: "pointer",
              color: active === l.id ? C.rust : "rgba(245,240,232,0.5)",
              fontWeight: active === l.id ? 600 : 400, transition: "color 0.3s",
            }}>{t(l.key)}</button>
          ))}
          <div style={{
            display: "flex", alignItems: "center",
            border: "1px solid rgba(255,255,255,0.12)", borderRadius: "4px",
            overflow: "hidden", marginLeft: "4px",
          }}>
            {LANGS.map((lang, idx) => (
              <button key={lang.code} onClick={() => i18n.changeLanguage(lang.code)} style={{
                fontFamily: "'DM Sans',sans-serif", fontSize: "10px", letterSpacing: "0.06em",
                padding: "4px 9px", border: "none", cursor: "pointer", transition: "all 0.25s",
                background: i18n.language === lang.code ? "rgba(255,255,255,0.13)" : "transparent",
                color: i18n.language === lang.code ? C.foam : "rgba(245,240,232,0.3)",
                fontWeight: i18n.language === lang.code ? 600 : 400,
                borderLeft: idx > 0 ? "1px solid rgba(255,255,255,0.1)" : "none",
              }}>{lang.label}</button>
            ))}
          </div>
          <a href={BOOKING} target="_blank" rel="noopener noreferrer" onClick={trackContact} style={{
            fontFamily: "'DM Sans',sans-serif", fontSize: "11px", letterSpacing: "0.05em",
            textTransform: "uppercase", color: C.foam, background: C.rust,
            padding: "7px 14px", borderRadius: "5px", textDecoration: "none", fontWeight: 600,
          }}>{t("nav.book")}</a>
        </div>
      </nav>

      {/* HERO */}
      <section id="hero" style={{
        position: "relative", height: "100vh", minHeight: "520px", overflow: "hidden", background: C.deep,
      }}>
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg,#1a2a3a 0%,#2C3E50 30%,#3D4F5F 60%,#1a2a3a 100%)" }} />
        <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse at 30% 80%, rgba(184,98,76,0.15) 0%, transparent 60%)" }} />
        <div style={{
          position: "absolute", bottom: "13%", left: "28px", right: "28px", zIndex: 10,
          opacity: loaded ? 1 : 0, transform: loaded ? "translateY(0)" : "translateY(25px)",
          transition: "all 0.8s ease 0.3s",
        }}>
          <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "11px", letterSpacing: "0.25em", textTransform: "uppercase", color: C.rust, marginBottom: "12px" }}>
            {t("hero.subtitle")}
          </div>
          <h1 style={{
            fontFamily: "'Playfair Display',serif", fontSize: "clamp(32px,6vw,64px)",
            fontWeight: 400, color: C.foam, lineHeight: 1.05, margin: 0, maxWidth: "600px",
          }}>{t("hero.title1")}<br />{t("hero.title2")}</h1>
          <p style={{
            fontFamily: "'DM Sans',sans-serif", fontSize: "15px", color: "rgba(245,240,232,0.5)",
            marginTop: "16px", maxWidth: "440px", lineHeight: 1.7,
          }}>
            {t("hero.description")}
          </p>
          <div style={{ display: "flex", gap: "12px", marginTop: "26px", flexWrap: "wrap" }}>
            <button onClick={() => go("oplevelser")} style={{
              fontFamily: "'DM Sans',sans-serif", fontSize: "13px", fontWeight: 600,
              color: C.foam, background: C.rust, border: "none", padding: "12px 24px",
              borderRadius: "7px", cursor: "pointer",
            }}>{t("hero.exploreBtn")}</button>
            <button onClick={() => go("huset")} style={{
              fontFamily: "'DM Sans',sans-serif", fontSize: "13px", fontWeight: 500,
              color: C.foam, background: "rgba(255,255,255,0.07)",
              border: "1px solid rgba(255,255,255,0.15)",
              padding: "12px 24px", borderRadius: "7px", cursor: "pointer",
            }}>{t("hero.houseBtn")}</button>
          </div>
        </div>
      </section>

      {/* HOUSE */}
      <section id="huset" style={{ padding: "90px 28px", background: C.cloud }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "48px", alignItems: "center" }}>
          <div onClick={advanceImg} style={{
            position: "relative", borderRadius: "14px", overflow: "hidden",
            aspectRatio: "4/3", background: C.sand, cursor: "pointer",
          }}>
            {houseImages.map((img, i) => (
              <img key={i} src={img.src} alt={img.alt} loading={i === 0 ? "eager" : "lazy"} style={{
                position: "absolute", inset: 0, width: "100%", height: "100%",
                objectFit: "cover", opacity: hImg === i ? 1 : 0, transition: "opacity 1s",
              }} />
            ))}
            <div style={{
              position: "absolute", bottom: "14px", left: "50%", transform: "translateX(-50%)",
              display: "flex", gap: "4px", background: "rgba(0,0,0,0.3)",
              padding: "5px 9px", borderRadius: "10px", pointerEvents: "none",
            }}>
              {houseImages.map((_img, i) => (
                <div key={i} style={{
                  width: hImg === i ? "16px" : "5px", height: "5px", borderRadius: "3px",
                  transition: "all 0.3s",
                  background: hImg === i ? C.rust : "rgba(255,255,255,0.45)",
                }} />
              ))}
            </div>
            <div style={{
              position: "absolute", bottom: "14px", right: "14px", pointerEvents: "none",
              fontFamily: "'DM Sans',sans-serif", fontSize: "11px", color: "white",
              background: "rgba(0,0,0,0.35)", padding: "3px 8px", borderRadius: "4px",
            }}>
              {(hImg + 1) + " / " + houseImages.length}
            </div>
          </div>
          <div>
            <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "11px", letterSpacing: "0.22em", textTransform: "uppercase", color: C.rust, marginBottom: "8px" }}>
              {t("house.address")}
            </div>
            <h2 style={{ fontFamily: "'Playfair Display',serif", fontSize: "clamp(24px,3.5vw,36px)", fontWeight: 400, color: C.deep, margin: "0 0 16px", lineHeight: 1.2 }}>
              {t("house.heading1")}<br /><em style={{ fontStyle: "italic" }}>{t("house.heading2")}</em>
            </h2>
            <p style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "14px", color: C.storm, lineHeight: 1.7, marginBottom: "22px", opacity: 0.8 }}>
              {t("house.description")}
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "7px", marginBottom: "22px" }}>
              {features.map((f, i) => (
                <div key={i} style={{
                  padding: "8px 11px", background: "rgba(255,255,255,0.7)", borderRadius: "7px",
                  fontFamily: "'DM Sans',sans-serif", fontSize: "12px", color: C.deep,
                }}>{f}</div>
              ))}
            </div>
            <div style={{ display: "flex", gap: "14px", marginBottom: "22px", fontFamily: "'DM Sans',sans-serif", fontSize: "11px", color: C.driftwood, flexWrap: "wrap" }}>
              <span>{t("house.size")}</span><span>{"\u00B7"}</span><span>{t("house.built")}</span><span>{"\u00B7"}</span><span>{t("house.renovated")}</span><span>{"\u00B7"}</span><span>{t("house.bedrooms")}</span>
            </div>
            <p style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "13px", color: C.storm, lineHeight: 1.7, marginBottom: "22px", opacity: 0.7 }}>
              {t("house.bookingNote")}
            </p>
            <a href={BOOKING} target="_blank" rel="noopener noreferrer" onClick={trackContact} style={{
              display: "inline-flex", alignItems: "center", gap: "8px",
              background: C.deep, color: C.foam, padding: "14px 26px",
              borderRadius: "8px", fontFamily: "'DM Sans',sans-serif", fontSize: "13px",
              fontWeight: 600, textDecoration: "none",
            }}>{t("house.bookBtn")}</a>
          </div>
        </div>
      </section>

      {/* CONTENT */}
      <section id="oplevelser" style={{ padding: "100px 28px 72px", background: C.foam }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
          <div style={{ marginBottom: "40px" }}>
            <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "11px", letterSpacing: "0.25em", textTransform: "uppercase", color: C.rust, marginBottom: "8px" }}>
              {t("experiences.updated")}
            </div>
            <h2 style={{ fontFamily: "'Playfair Display',serif", fontSize: "clamp(24px,4vw,38px)", fontWeight: 400, color: C.deep, margin: 0, lineHeight: 1.15 }}>
              {t("experiences.heading1")}<em style={{ fontStyle: "italic", color: C.sea }}>{t("experiences.heading2")}</em>
            </h2>
          </div>
          <div style={{ display: "flex", gap: "7px", marginBottom: "32px", flexWrap: "wrap" }}>
            <button onClick={() => { setCat("all"); setShowAll(false); }} style={{
              padding: "7px 16px", borderRadius: "100px", border: "none",
              fontFamily: "'DM Sans',sans-serif", fontSize: "12px", cursor: "pointer",
              transition: "all 0.25s",
              background: cat === "all" ? C.deep : "rgba(44,62,80,0.06)",
              color: cat === "all" ? C.foam : C.storm,
              fontWeight: cat === "all" ? 600 : 400,
            }}>{"◈ " + t("experiences.allFilter")}</button>
            {categories.map((c) => {
              const label = c.translations[i18n.language]?.label ?? c.translations["da"]?.label ?? c.id;
              return (
                <button key={c.id} onClick={() => { setCat(c.id); setShowAll(false); }} style={{
                  padding: "7px 16px", borderRadius: "100px", border: "none",
                  fontFamily: "'DM Sans',sans-serif", fontSize: "12px", cursor: "pointer",
                  transition: "all 0.25s",
                  background: cat === c.id ? C.deep : "rgba(44,62,80,0.06)",
                  color: cat === c.id ? C.foam : C.storm,
                  fontWeight: cat === c.id ? 600 : 400,
                }}>{c.icon + " " + label}</button>
              );
            })}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(300px,1fr))", gap: "20px" }}>
            {loading ? [0, 1, 2].map((i) => (
              <div key={i} style={{
                background: "white", borderRadius: "12px", overflow: "hidden",
                animation: "pulse 1.5s ease-in-out infinite",
              }}>
                <div style={{ height: "100px", background: "rgba(44,62,80,0.06)" }} />
                <div style={{ padding: "20px 22px 24px" }}>
                  <div style={{ height: "10px", width: "60px", background: "rgba(44,62,80,0.08)", borderRadius: "4px", marginBottom: "12px" }} />
                  <div style={{ height: "16px", width: "80%", background: "rgba(44,62,80,0.08)", borderRadius: "4px", marginBottom: "10px" }} />
                  <div style={{ height: "12px", width: "100%", background: "rgba(44,62,80,0.05)", borderRadius: "4px", marginBottom: "6px" }} />
                  <div style={{ height: "12px", width: "70%", background: "rgba(44,62,80,0.05)", borderRadius: "4px" }} />
                </div>
              </div>
            )) : displayed.map((item, i) => <Card key={item.id} item={item} idx={i} />)}
          </div>
          {filtered.length > 6 && !showAll ? (
            <div style={{ textAlign: "center", marginTop: "40px" }}>
              <button onClick={() => setShowAll(true)} style={{
                fontFamily: "'DM Sans',sans-serif", fontSize: "13px", fontWeight: 600,
                color: C.deep, background: "rgba(44,62,80,0.06)",
                border: "1px solid rgba(44,62,80,0.1)", padding: "12px 28px",
                borderRadius: "8px", cursor: "pointer",
              }}>{t("experiences.showAll", { count: filtered.length })}</button>
            </div>
          ) : null}
          <div style={{ textAlign: "center", marginTop: showAll || filtered.length <= 6 ? "40px" : "16px" }}>
            <button onClick={() => { setShowArchive(!showArchive); if (!showArchive) loadArchive(); }} style={{
              fontFamily: "'DM Sans',sans-serif", fontSize: "11px",
              color: C.driftwood, background: "none", border: "none",
              cursor: "pointer", opacity: 0.6, transition: "opacity 0.2s",
            }}>{showArchive ? t("experiences.hideArchive") : t("experiences.showArchive")}</button>
          </div>
          {showArchive && archivedPosts.length > 0 ? (
            <div style={{ marginTop: "28px", paddingTop: "28px", borderTop: "1px solid rgba(44,62,80,0.08)" }}>
              <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "11px", letterSpacing: "0.15em", textTransform: "uppercase", color: C.driftwood, marginBottom: "16px", opacity: 0.6 }}>
                {t("experiences.archiveLabel")}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(300px,1fr))", gap: "20px", opacity: 0.65 }}>
                {archivedPosts.map((item, i) => <Card key={item.id} item={item} idx={i} />)}
              </div>
            </div>
          ) : null}
        </div>
      </section>

      {/* AREAS */}
      <section id="omraadet" style={{ padding: "90px 28px", background: C.foam }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
          <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "11px", letterSpacing: "0.25em", textTransform: "uppercase", color: C.rust, marginBottom: "8px" }}>
            {t("areas.subtitle")}
          </div>
          <h2 style={{ fontFamily: "'Playfair Display',serif", fontSize: "clamp(24px,4vw,38px)", fontWeight: 400, color: C.deep, margin: "0 0 40px" }}>
            {t("areas.heading1")}<em style={{ fontStyle: "italic", color: C.sea }}>{t("areas.heading2")}</em>
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(230px,1fr))", gap: "14px" }}>
            {loading ? [0, 1, 2, 3].map((i) => (
              <div key={i} style={{
                padding: "24px", background: "white", borderRadius: "11px",
                border: "1px solid rgba(212,197,169,0.3)",
                animation: "pulse 1.5s ease-in-out infinite",
              }}>
                <div style={{ height: "10px", width: "80px", background: "rgba(44,62,80,0.08)", borderRadius: "4px", marginBottom: "8px" }} />
                <div style={{ height: "16px", width: "70%", background: "rgba(44,62,80,0.08)", borderRadius: "4px", marginBottom: "10px" }} />
                <div style={{ height: "12px", width: "100%", background: "rgba(44,62,80,0.05)", borderRadius: "4px" }} />
              </div>
            )) : areas.map((area) => {
              const atr = area.translations[i18n.language] ?? area.translations["da"];
              return (
                <a key={area.id} href={area.url} target="_blank" rel="noopener noreferrer" style={{
                  padding: "24px", background: "white", borderRadius: "11px",
                  border: "1px solid rgba(212,197,169,0.3)", textDecoration: "none", display: "block",
                }}>
                  <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "10px", color: C.rust, letterSpacing: "0.06em", marginBottom: "5px", textTransform: "uppercase" }}>{atr?.dist}</div>
                  <h3 style={{ fontFamily: "'Playfair Display',serif", fontSize: "19px", fontWeight: 500, color: C.deep, margin: "0 0 7px" }}>{atr?.name}</h3>
                  <p style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "13px", color: C.storm, lineHeight: 1.55, margin: 0, opacity: 0.72 }}>{atr?.desc}</p>
                </a>
              );
            })}
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer style={{ padding: "48px 28px 80px", background: C.deep, color: "rgba(245,240,232,0.4)" }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto", display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: "36px" }}>
          <div>
            <div style={{ fontFamily: "'Playfair Display',serif", fontSize: "20px", color: C.foam, marginBottom: "10px" }}>{t("nav.brand")}</div>
            <p style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "12px", lineHeight: 1.6, maxWidth: "280px" }}>
              {t("footer.tagline")}
            </p>
          </div>
          <div>
            <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "10px", letterSpacing: "0.14em", textTransform: "uppercase", color: C.rust, marginBottom: "12px" }}>{t("footer.pages")}</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "7px" }}>
              {navLinks.map((l) => (
                <button key={l.id} onClick={() => go(l.id)} style={{ color: "rgba(245,240,232,0.4)", background: "none", border: "none", cursor: "pointer", fontFamily: "'DM Sans',sans-serif", fontSize: "12px", textAlign: "left", padding: 0 }}>{t(l.key)}</button>
              ))}
            </div>
          </div>
          <div>
            <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "10px", letterSpacing: "0.14em", textTransform: "uppercase", color: C.rust, marginBottom: "12px" }}>{t("footer.explore")}</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "7px", fontFamily: "'DM Sans',sans-serif", fontSize: "12px" }}>
              <a href="https://eng.nationalparkthy.dk" target="_blank" rel="noopener noreferrer" style={{ color: "inherit", textDecoration: "none" }}>{"Nationalpark Thy"}</a>
              <a href="https://www.visit-nordvestkysten.com" target="_blank" rel="noopener noreferrer" style={{ color: "inherit", textDecoration: "none" }}>{"VisitNordvestkysten"}</a>
              <a href="https://coldhawaiisurfcamp.com" target="_blank" rel="noopener noreferrer" style={{ color: "inherit", textDecoration: "none" }}>{"Cold Hawaii Surf Camp"}</a>
              <a href="https://www.jesperhus.dk" target="_blank" rel="noopener noreferrer" style={{ color: "inherit", textDecoration: "none" }}>{"Jesperhus"}</a>
            </div>
          </div>
          <div>
            <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "10px", letterSpacing: "0.14em", textTransform: "uppercase", color: C.rust, marginBottom: "12px" }}>{t("footer.contact")}</div>
            <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: "12px", lineHeight: 2 }}>
              <a href="https://www.aggerferiehuse.dk" target="_blank" rel="noopener noreferrer" style={{ color: "inherit", textDecoration: "none" }}>{"Agger Feriehuse"}</a>
              <div style={{ opacity: 0.6, fontSize: "11px", lineHeight: 1.5, marginTop: "4px" }}>{t("footer.contactNote")}</div>
            </div>
          </div>
        </div>
        <div style={{ maxWidth: "1200px", margin: "36px auto 0", paddingTop: "18px", borderTop: "1px solid rgba(245,240,232,0.07)", fontFamily: "'DM Sans',sans-serif", fontSize: "11px", display: "flex", justifyContent: "space-between" }}>
          <span>{t("footer.copyright")}</span>
          <span>{t("footer.bookingVia")}
            <a href="https://www.aggerferiehuse.dk" target="_blank" rel="noopener noreferrer" onClick={trackContact} style={{ color: C.rust, textDecoration: "none" }}>{"aggerferiehuse.dk"}</a>
          </span>
        </div>
      </footer>

      {/* STICKY */}
      <div style={{
        position: "fixed", bottom: 0, left: 0, right: 0, zIndex: 1000,
        transform: sticky ? "translateY(0)" : "translateY(100%)",
        transition: "transform 0.4s cubic-bezier(0.22,1,0.36,1)",
        background: "linear-gradient(135deg," + C.deep + "," + C.storm + ")",
        backdropFilter: "blur(20px)", borderTop: "1px solid rgba(255,255,255,0.1)",
        padding: "10px 22px", display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "9px" }}>
          <div style={{ width: "7px", height: "7px", borderRadius: "50%", background: C.rust, animation: "pulse 2s infinite" }} />
          <span style={{ fontFamily: "'DM Sans',sans-serif", color: C.foam, fontSize: "12px" }}>{t("sticky.text")}</span>
        </div>
        <a href={BOOKING} target="_blank" rel="noopener noreferrer" onClick={trackContact} style={{
          background: C.rust, color: C.foam, padding: "8px 18px", borderRadius: "5px",
          fontFamily: "'DM Sans',sans-serif", fontSize: "11px", fontWeight: 600,
          letterSpacing: "0.04em", textTransform: "uppercase", textDecoration: "none", whiteSpace: "nowrap",
        }}>{t("sticky.cta")}</a>
      </div>
    </div>
  );
}

export default App;
