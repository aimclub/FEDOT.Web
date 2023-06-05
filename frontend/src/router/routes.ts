export enum AppRoutesEnum {
  SIGNIN = "/",
  SIGNUP = "register",
  WORKSPACE = "/ws",
  SHOWCASE = "showcase",
  SANDBOX = "sandbox",
  CASE = ":caseId",
  HISTORY = "history",
  SETTING = "settings",
}

export const goToPage = {
  showcase: `${AppRoutesEnum.WORKSPACE}/${AppRoutesEnum.SHOWCASE}`,
  sandbox: (caseId: string) =>
    `${AppRoutesEnum.WORKSPACE}/${AppRoutesEnum.SANDBOX}/${caseId}`,
  history: (caseId?: string) =>
    caseId
      ? `${AppRoutesEnum.WORKSPACE}/${AppRoutesEnum.SANDBOX}/${caseId}/${AppRoutesEnum.HISTORY}`
      : AppRoutesEnum.HISTORY,
  settings: `${AppRoutesEnum.WORKSPACE}/${AppRoutesEnum.SETTING}`,
};

export const GITHUB_LINK = "https://github.com/nccr-itmo/FEDOT";
