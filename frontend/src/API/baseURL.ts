import axios from "axios";

const BASE_URL = "https://10.9.14.122:5000/api";

export const instance = axios.create({
  baseURL: `${BASE_URL}`,
  // withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});
