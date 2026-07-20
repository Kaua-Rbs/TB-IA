import { normalizeLanguage, type Language } from "./i18n";

export interface ScenarioRow {
  rule_id: string;
  ranking_dimension?: string;
  comparison_scope?: string;
  indicator_id: string;
  severity: string;
  score: number;
  explanation: string;
  indicator_value?: number | null;
  threshold_value?: number | null;
}

export interface IndicatorValue {
  name?: string;
  indicator_name?: string;
  value: number | null;
  is_suppressed?: boolean;
  unit?: string | null;
  direction?: string | null;
}

export interface MunicipalityProperties {
  territory_id: string;
  name: string;
  uf?: string;
  priority_score: number;
  scenario_count: number;
  ranking_dimension_count?: number;
  top_severity: string | null;
  top_explanations: string[];
  top_scenarios: ScenarioRow[];
  data_status: string;
  indicators: Record<string, IndicatorValue>;
  layer_value?: number | null;
  layer_bucket?: string;
}

export interface GeoFeature<TProperties = MunicipalityProperties> {
  type: "Feature";
  properties: TProperties;
  geometry: GeoGeometry | null;
}

export interface GeoGeometry {
  type: string;
  coordinates: unknown;
}

export interface MapLayerDefinition {
  label: string;
  kind: string;
  unit?: string | null;
  direction?: string | null;
}

export interface MapMetadata {
  uf?: string;
  geographic_scope?: string;
  comparison_scope?: string;
  year?: number;
  feature_count: number;
  drawable_geometry_count: number;
  layers?: Record<string, MapLayerDefinition>;
  caveat?: string;
  status?: string;
  data_level?: string;
  parent_id?: string;
  territory_type?: string;
}

export interface FeatureCollection<TProperties = MunicipalityProperties> {
  type: "FeatureCollection";
  metadata: MapMetadata;
  features: Array<GeoFeature<TProperties>>;
}

export interface RankingRow {
  territory_id: string;
  territory_name: string;
  score: number;
  scenario_count: number;
  ranking_dimension_count?: number;
  top_severity: string | null;
  top_explanations: string[];
  top_scenarios: ScenarioRow[];
}

export interface ReadinessItem {
  label: string;
  status: string;
  detail: string;
  [key: string]: string | number | boolean | null | undefined;
}

export interface MonthCoverage {
  expected_months: number[];
  loaded_months: number[] | null;
  missing_months: number[] | null;
  complete: boolean;
  scope_count: number;
  complete_scope_count: number;
}

export interface SourceRow {
  source_id: string;
  name: string;
  status: string;
  row_count: number;
  finished_at: string | null;
  message: string;
  caveats: string;
  year: number | null;
  geographic_scope: string | null;
  scope_inherited: boolean;
  month_coverage: MonthCoverage | null;
}

export interface TerritorialContext {
  uf: string;
  geographic_scope: string;
  comparison_scope: string;
  year: number;
  territory_count: number;
  indicator_count: number;
  scenario_count: number;
  readiness: Record<string, ReadinessItem>;
  health_territory_readiness: Record<string, ReadinessItem>;
  ranking: RankingRow[];
  sources: SourceRow[];
  caveat: string;
}

export interface ReportIndicator extends IndicatorValue {
  indicator_id: string;
  indicator_name: string;
}

export interface RecommendationRow {
  strategy_id?: string;
  rule_id?: string;
  trigger_rule_ids?: string[];
  recommendation_id?: string;
  title?: string;
  action?: string;
  explanation?: string;
  priority?: string;
}

export interface TerritoryReport {
  territory_id: string;
  territory_name: string;
  year: number;
  comparison_scope?: string;
  indicators: ReportIndicator[];
  recommendations: RecommendationRow[];
  scenarios?: ScenarioRow[];
  caveats?: string[];
}

export interface OperationsSummary {
  year: number;
  case_count: number;
  alert_count: number;
  open_alert_count: number;
  by_type: Array<{ alert_type: string; count: number }>;
  by_severity: Array<{ severity: string; count: number }>;
  by_status: Array<{ status: string; count: number }>;
  by_facility_team: FacilityTeamSummary[];
}

export interface FacilityTeamSummary {
  facility_id: string;
  team_id: string;
  team_name: string;
  alert_count: number;
  high: number;
  moderate: number;
  open: number;
}

export interface OperationalAlert {
  alert_id: string;
  year: number;
  alert_type: string;
  severity: string;
  status: string;
  local_case_id: string;
  territory_id: string;
  facility_id: string;
  team_id: string;
  team_name: string;
  related_entity_id: string | null;
  reference_date: string;
  generated_at: string;
  due_date: string | null;
  message: string;
}

export interface LoadYearJob {
  job_id: string;
  uf: string;
  year: number;
  sih_all_months: boolean;
  status: "queued" | "running" | "complete" | "failed";
  result_status: string | null;
  stage: string;
  step_index: number;
  step_count: number;
  message: string;
  download: {
    requested_file_count: number;
    downloaded_file_count: number;
    existing_file_count: number;
    failed_file_count: number;
    failures: Array<{
      source_id: string;
      label: string;
      url: string;
      message: string;
    }>;
    sih_all_months: boolean;
  } | null;
  indicator_count: number;
  scenario_count: number;
  recommendation_count: number;
  error: string | null;
  created_at: string;
  started_at: string | null;
  updated_at: string;
  finished_at: string | null;
}

interface TerritorialParams {
  uf: string;
  year: number;
  comparisonScope: string;
  lang: Language;
}

interface OperationFilters {
  year: number;
  lang?: Language;
  alertType?: string;
  severity?: string;
  facilityId?: string;
  teamId?: string;
  status?: string;
}

function queryString(
  params: Record<string, string | number | null | undefined>,
) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value));
    }
  }
  return query.toString();
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

async function postJson<T>(path: string): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function fetchTerritorialContext(params: TerritorialParams) {
  return getJson<TerritorialContext>(
    `/api/territorial/context?${queryString({
      uf: params.uf,
      year: params.year,
      comparison_scope: params.comparisonScope,
      lang: normalizeLanguage(params.lang),
    })}`,
  );
}

export function fetchTerritorialMap(params: TerritorialParams) {
  return getJson<FeatureCollection>(
    `/api/territorial/map?${queryString({
      uf: params.uf,
      year: params.year,
      comparison_scope: params.comparisonScope,
      lang: normalizeLanguage(params.lang),
    })}`,
  );
}

export function startTerritorialYearLoad(
  params: TerritorialParams & { sihAllMonths: boolean },
) {
  return postJson<LoadYearJob>(
    `/api/territorial/load-year?${queryString({
      uf: params.uf,
      year: params.year,
      lang: normalizeLanguage(params.lang),
      sih_all_months: params.sihAllMonths ? "true" : "false",
    })}`,
  );
}

export function fetchTerritorialYearLoadJob(jobId: string) {
  return getJson<LoadYearJob>(
    `/api/territorial/load-year/${encodeURIComponent(jobId)}`,
  );
}

export function fetchSubterritories(parentId: string, lang: Language) {
  return getJson<FeatureCollection>(
    `/api/territorial/subterritories?${queryString({
      parent_id: parentId,
      territory_type: "neighborhood_reference",
      lang,
    })}`,
  );
}

export function fetchTerritoryReport(
  territoryId: string,
  year: number,
  comparisonScope: string,
  lang: Language,
) {
  return getJson<TerritoryReport>(
    `/api/territories/${encodeURIComponent(territoryId)}/report?${queryString({
      year,
      comparison_scope: comparisonScope,
      lang,
    })}`,
  );
}

export function fetchOperationsSummary(year: number) {
  return getJson<OperationsSummary>(
    `/api/operations/summary?${queryString({ year })}`,
  );
}

export function fetchOperationAlerts(filters: OperationFilters) {
  return getJson<OperationalAlert[]>(
    `/api/operations/alerts?${queryString({
      year: filters.year,
      alert_type: filters.alertType,
      severity: filters.severity,
      facility_id: filters.facilityId,
      team_id: filters.teamId,
      status: filters.status,
      lang: normalizeLanguage(filters.lang ?? "pt"),
    })}`,
  );
}

export function fetchOperationAlert(alertId: string, lang: Language = "pt") {
  return getJson<OperationalAlert>(
    `/api/operations/alerts/${encodeURIComponent(alertId)}?${queryString({
      lang: normalizeLanguage(lang),
    })}`,
  );
}
