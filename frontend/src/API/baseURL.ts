// import axios from "axios";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/dist/query/react";

const BASE_URL: string | undefined = process.env.REACT_APP_BASE_URL;

// export const instance = axios.create({
//   baseURL: `${BASE_URL}/api`,
//   headers: {
//     "Content-Type": "application/json",
//   },
// });

export const staticAPI = {
  getImage: (imgPath: string) => `${BASE_URL}${imgPath}`,
};

export const commonApi = createApi({
  reducerPath: "api",
  baseQuery: fetchBaseQuery({
    baseUrl: `${BASE_URL}/api`,
  }),
  tagTypes: ["case"],
  endpoints: () => ({}),
});
