import { ActivitySquare, Database, Languages, MapPinned, Menu, X } from 'lucide-react';
import { useEffect, useState, type ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';

import susSymbol from '../assets/mockup-icons/sus-symbol.svg';
import tbiaLockup from '../assets/mockup-icons/tbia-lockup.svg';
import { copy, normalizeLanguage } from '../lib/i18n';

interface ShellProps {
  children: ReactNode;
}

export function Shell({ children }: ShellProps) {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const searchParams = new URLSearchParams(location.search);
  const lang = normalizeLanguage(searchParams.get('lang'));
  const labels = copy[lang];
  const search = location.search || `?lang=${lang}`;
  const otherLang = lang === 'pt' ? 'en' : 'pt';
  const languageParams = new URLSearchParams(location.search);
  languageParams.set('lang', otherLang);
  const languagePath = `${location.pathname || '/territorios'}?${languageParams.toString()}${location.hash}`;

  useEffect(() => {
    setIsMenuOpen(false);
  }, [location.hash, location.pathname, location.search]);

  return (
    <div className="product-shell">
      <aside className="sidebar" aria-label="TB-IA">
        <a className="brand" href={`/territorios${search}`} onClick={() => setIsMenuOpen(false)}>
          <img className="brand-lockup" src={tbiaLockup} alt={`${labels.appName} — ${labels.appSubtitle}`} />
          <span className="brand-context">{labels.productContext}</span>
        </a>
        <button
          type="button"
          className="mobile-menu-button"
          aria-label={isMenuOpen ? labels.closeMenu : labels.openMenu}
          aria-expanded={isMenuOpen}
          aria-controls="product-navigation-panel"
          onClick={() => setIsMenuOpen((value) => !value)}
        >
          {isMenuOpen ? <X size={22} aria-hidden="true" /> : <Menu size={22} aria-hidden="true" />}
        </button>
        <div
          id="product-navigation-panel"
          className={`shell-navigation ${isMenuOpen ? 'open' : ''}`}
        >
          <div className="navigation-heading">{labels.navigationLabel}</div>
          <nav className="primary-nav" aria-label={labels.navigationLabel}>
            <NavLink to={`/territorios${search}`} onClick={() => setIsMenuOpen(false)}>
              <MapPinned size={18} aria-hidden="true" />
              <span>{labels.nav.territorial}</span>
            </NavLink>
            <NavLink to={`/acompanhamento${search}`} onClick={() => setIsMenuOpen(false)}>
              <ActivitySquare size={18} aria-hidden="true" />
              <span>{labels.nav.operations}</span>
            </NavLink>
            <a href={`/territorios${search}#dados`} onClick={() => setIsMenuOpen(false)}>
              <Database size={18} aria-hidden="true" />
              <span>{labels.nav.governance}</span>
            </a>
          </nav>
          <div className="sidebar-footer">
            <div className="shell-evidence">
              <span>{labels.evidenceBoundary}</span>
              <img src={susSymbol} alt={labels.concept.susName} />
            </div>
            <a className="language-switch" href={languagePath} onClick={() => setIsMenuOpen(false)}>
              <Languages size={17} aria-hidden="true" />
              <span>{labels.languageToggle}</span>
            </a>
          </div>
        </div>
      </aside>
      <main className="app-main">{children}</main>
    </div>
  );
}
