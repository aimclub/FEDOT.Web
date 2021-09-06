import axios from "axios";

const BASE_URL = "http://10.32.1.9:5000/api";

export const instance = axios.create({
  baseURL: `${BASE_URL}`,
  // withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});
