import type { ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';

import susSymbol from '../assets/mockup-icons/sus-symbol.svg';
import tbiaLockup from '../assets/mockup-icons/tbia-lockup.svg';
import { copy, normalizeLanguage } from '../lib/i18n';
import { ConceptIcon } from './ConceptIcon';

interface ConceptShellProps {
  children: ReactNode;
}

export function ConceptShell({ children }: ConceptShellProps) {
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const lang = normalizeLanguage(searchParams.get('lang'));
  const labels = copy[lang];
  const search = location.search || `?lang=${lang}`;
  const otherLang = lang === 'pt' ? 'en' : 'pt';
  const languageParams = new URLSearchParams(location.search);
  languageParams.set('lang', otherLang);
  const languagePath = `${location.pathname || '/conceito/territorios'}?${languageParams.toString()}${location.hash}`;

  return (
    <div className="concept-shell">
      <aside className="concept-sidebar" aria-label="TB-IA">
        <a
          className="concept-brand"
          href={`/conceito/territorios${search}`}
          aria-label={`${labels.appName} - ${labels.concept.managerConsole}`}
        >
          <img
            className="concept-brand-lockup"
            src={tbiaLockup}
            alt={`${labels.appName} - ${labels.concept.managerConsole}`}
          />
        </a>
        <nav className="concept-nav" aria-label="Principal">
          <NavLink to={`/conceito/territorios${search}`}>
            <ConceptIcon name="territory" size={18} />
            <span>{labels.nav.territorial}</span>
          </NavLink>
          <NavLink to={`/conceito/acompanhamento${search}`}>
            <ConceptIcon name="followUp" size={18} />
            <span>{labels.nav.operations}</span>
          </NavLink>
          <a href={`/conceito/territorios${search}#dados`}>
            <ConceptIcon name="publicData" size={18} />
            <span>{labels.concept.publicData}</span>
          </a>
          <a href={`/conceito/acompanhamento${search}#alertas`}>
            <ConceptIcon name="alerts" size={18} />
            <span>{labels.concept.alerts}</span>
          </a>
          <a href={`/conceito/territorios${search}#relatorios`}>
            <ConceptIcon name="reports" size={18} />
            <span>{labels.concept.reports}</span>
          </a>
          <a href={`/conceito/territorios${search}#territorios-saude`}>
            <ConceptIcon name="healthTerritory" size={18} />
            <span>{labels.territorial.healthTerritories}</span>
          </a>
          <a href={`/conceito/territorios${search}#usuarios`}>
            <ConceptIcon name="userManagement" size={18} />
            <span>{labels.concept.userManagement}</span>
          </a>
          <a href={`/conceito/territorios${search}#configuracoes`}>
            <ConceptIcon name="settings" size={18} />
            <span>{labels.concept.settings}</span>
          </a>
        </nav>
        <div className="concept-sidebar-footer">
          <a className="concept-help-link" href={`/conceito/territorios${search}#ajuda`}>
            <ConceptIcon name="help" size={16} />
            <span>{labels.concept.help}</span>
          </a>
          <a className="concept-language" href={languagePath}>
            <ConceptIcon name="language" size={15} />
            <span>{labels.languageToggle}</span>
          </a>
          <div className="concept-sus-badge" aria-label={labels.concept.susName}>
            <span>{labels.concept.ministryOfHealth}</span>
            <img className="concept-sus-logo" src={susSymbol} alt={labels.concept.susName} />
          </div>
        </div>
      </aside>
      <main className="concept-main">{children}</main>
    </div>
  );
}
