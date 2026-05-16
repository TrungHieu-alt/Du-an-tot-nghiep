export const LOCATION_LABELS: Record<string, string> = {
  ha_noi: "Hà Nội", tp_hcm: "TP HCM", da_nang: "Đà Nẵng",
};
export const JOB_TYPE_LABELS: Record<string, string> = {
  remote: "Từ xa", fulltime: "Toàn thời gian", parttime: "Bán thời gian",
};
export const SENIORITY_LABELS: Record<string, string> = {
  intern: "Thực tập", fresher: "Fresher", junior: "Junior",
  mid: "Mid", senior: "Senior", lead: "Lead",
};
export const EDUCATION_LABELS: Record<string, string> = {
  lop_9: "Lớp 9", lop_12: "Lớp 12", dai_hoc: "Đại học",
  thac_si: "Thạc sĩ", tien_si: "Tiến sĩ",
};
export const RESUME_STATUS_LABELS: Record<string, string> = {
  draft: "Nháp", active: "Đang hoạt động", archived: "Đã lưu trữ",
};
export const JOB_STATUS_LABELS: Record<string, string> = {
  draft: "Nháp", published: "Đã đăng", closed: "Đã đóng",
};
export const APP_STATUS_LABELS: Record<string, string> = {
  submitted: "Đã nộp", shortlisted: "Được chọn",
  rejected: "Bị từ chối", hired: "Được tuyển", withdrawn: "Đã rút",
};
export const INVITE_STATUS_LABELS: Record<string, string> = {
  pending: "Đang chờ", accepted: "Đã chấp nhận", rejected: "Đã từ chối",
};
export const LOCATIONS = ["ha_noi", "tp_hcm", "da_nang"] as const;
export const JOB_TYPES = ["remote", "fulltime", "parttime"] as const;
export const SENIORITIES = ["intern", "fresher", "junior", "mid", "senior", "lead"] as const;
export const EDUCATIONS = ["lop_9", "lop_12", "dai_hoc", "thac_si", "tien_si"] as const;
