import type { CSSProperties } from 'react';

import actionCloseIcon from '../assets/mockup-icons/action-close.svg';
import actionCollapseIcon from '../assets/mockup-icons/action-collapse.svg';
import actionExpandIcon from '../assets/mockup-icons/action-expand.svg';
import actionExportIcon from '../assets/mockup-icons/action-export.svg';
import actionFilterIcon from '../assets/mockup-icons/action-filter.svg';
import actionLanguageIcon from '../assets/mockup-icons/action-language.svg';
import actionRefreshIcon from '../assets/mockup-icons/action-refresh.svg';
import actionSearchIcon from '../assets/mockup-icons/action-search.svg';
import featureCareManagementIcon from '../assets/mockup-icons/feature-care-management.svg';
import featureResponsiveExperienceIcon from '../assets/mockup-icons/feature-responsive-experience.svg';
import featureTerritorialVisionIcon from '../assets/mockup-icons/feature-territorial-vision.svg';
import mapSelectedMunicipalityIcon from '../assets/mockup-icons/map-selected-municipality.svg';
import mapZoomInIcon from '../assets/mockup-icons/map-zoom-in.svg';
import mapZoomOutIcon from '../assets/mockup-icons/map-zoom-out.svg';
import menuIcon from '../assets/mockup-icons/menu.svg';
import navAlertsIcon from '../assets/mockup-icons/nav-alerts.svg';
import navCareFollowupIcon from '../assets/mockup-icons/nav-care-followup.svg';
import navHealthTerritoriesIcon from '../assets/mockup-icons/nav-health-territories.svg';
import navHelpIcon from '../assets/mockup-icons/nav-help.svg';
import navPublicDataIcon from '../assets/mockup-icons/nav-public-data.svg';
import navReportsIcon from '../assets/mockup-icons/nav-reports.svg';
import navSettingsIcon from '../assets/mockup-icons/nav-settings.svg';
import navTerritorialAnalysisIcon from '../assets/mockup-icons/nav-territorial-analysis.svg';
import navUserManagementIcon from '../assets/mockup-icons/nav-user-management.svg';
import priorityRankingIcon from '../assets/mockup-icons/priority-ranking.svg';
import readinessBarsIcon from '../assets/mockup-icons/readiness-bars.svg';
import signalCheckIcon from '../assets/mockup-icons/signal-check.svg';

const conceptIconPaths = {
  alert: navAlertsIcon,
  alerts: navAlertsIcon,
  careManagement: featureCareManagementIcon,
  check: signalCheckIcon,
  chevronDown: actionExpandIcon,
  chevronUp: actionCollapseIcon,
  close: actionCloseIcon,
  currentInterface: priorityRankingIcon,
  data: navPublicDataIcon,
  download: actionRefreshIcon,
  expand: actionExpandIcon,
  export: actionExportIcon,
  featureResponsive: featureResponsiveExperienceIcon,
  filter: actionFilterIcon,
  followUp: navCareFollowupIcon,
  healthTerritory: navHealthTerritoriesIcon,
  help: navHelpIcon,
  language: actionLanguageIcon,
  layers: navTerritorialAnalysisIcon,
  mapPin: mapSelectedMunicipalityIcon,
  menu: menuIcon,
  publicData: navPublicDataIcon,
  readiness: readinessBarsIcon,
  refresh: actionRefreshIcon,
  reports: navReportsIcon,
  search: actionSearchIcon,
  settings: navSettingsIcon,
  team: navUserManagementIcon,
  territory: navTerritorialAnalysisIcon,
  territorialVision: featureTerritorialVisionIcon,
  userManagement: navUserManagementIcon,
  zoomIn: mapZoomInIcon,
  zoomOut: mapZoomOutIcon,
} as const;

export type ConceptIconName = keyof typeof conceptIconPaths;

interface ConceptIconProps {
  name: ConceptIconName;
  size?: number;
  className?: string;
  label?: string;
}

export function ConceptIcon({
  name,
  size = 18,
  className = '',
  label,
}: ConceptIconProps) {
  const path = conceptIconPaths[name];
  const style: CSSProperties = {
    width: size,
    height: size,
    WebkitMaskImage: `url(${path})`,
    maskImage: `url(${path})`,
  };
  const classes = ['concept-icon', className].filter(Boolean).join(' ');

  return (
    <span
      className={classes}
      style={style}
      aria-hidden={label ? undefined : 'true'}
      aria-label={label}
      role={label ? 'img' : undefined}
    />
  );
}
