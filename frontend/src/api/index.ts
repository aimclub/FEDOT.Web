import axios from "axios";

const initializers = {
  // baseURL: 'https://10.9.14.122:5000/',
  headers: {
    "Content-Type": "application/json",
  },
};

export const instance = axios.create(initializers);
