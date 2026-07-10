import { ActivitySquare, Database, Languages, MapPinned } from 'lucide-react';
import type { ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';

import { copy, normalizeLanguage } from '../lib/i18n';

interface ShellProps {
  children: ReactNode;
}

export function Shell({ children }: ShellProps) {
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const lang = normalizeLanguage(searchParams.get('lang'));
  const labels = copy[lang];
  const search = location.search || `?lang=${lang}`;
  const otherLang = lang === 'pt' ? 'en' : 'pt';
  const languageParams = new URLSearchParams(location.search);
  languageParams.set('lang', otherLang);
  const languagePath = `${location.pathname || '/territorios'}?${languageParams.toString()}${location.hash}`;

  return (
    <div className="product-shell">
      <aside className="sidebar" aria-label="TB-IA">
        <a className="brand" href={`/territorios${search}`}>
          <span className="brand-mark">TB</span>
          <span>
            <strong>{labels.appName}</strong>
            <small>{labels.appSubtitle}</small>
          </span>
        </a>
        <nav className="primary-nav" aria-label="Principal">
          <NavLink to={`/territorios${search}`}>
            <MapPinned size={18} aria-hidden="true" />
            <span>{labels.nav.territorial}</span>
          </NavLink>
          <NavLink to={`/acompanhamento${search}`}>
            <ActivitySquare size={18} aria-hidden="true" />
            <span>{labels.nav.operations}</span>
          </NavLink>
          <a href={`/territorios${search}#dados`}>
            <Database size={18} aria-hidden="true" />
            <span>{labels.nav.governance}</span>
          </a>
        </nav>
        <a className="language-switch" href={languagePath}>
          <Languages size={17} aria-hidden="true" />
          <span>{labels.languageToggle}</span>
        </a>
      </aside>
      <main className="app-main">{children}</main>
    </div>
  );
}
