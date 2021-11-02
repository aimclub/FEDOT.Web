import axios from "axios";

const BASE_URL: string | undefined = process.env.REACT_APP_BASE_URL;

export const instance = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
});

export const staticAPI = {
  getImage: (imgPath: string) => `${BASE_URL}${imgPath}`,
};
