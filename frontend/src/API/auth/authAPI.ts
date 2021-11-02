import { AxiosError } from "axios";
import { instance } from "../baseURL";
import { IAuth, IResRegister } from "./authInterface";

export const authAPI = {
  async signIn(email: string, password: string) {
    try {
      const res = await instance.post<IAuth>(`/token/get_token`, {
        email,
        password,
      });
      return res.data;
    } catch (error) {
      return Promise.reject((error as AxiosError).response?.data || error);
    }
  },
  async signUp(email: string, password: string) {
    try {
      const res = await instance.post<IResRegister>(`/token/signup`, {
        email,
        password,
      });
      return res.data;
    } catch (error) {
      return Promise.reject((error as AxiosError).response?.data || error);
    }
  },
};
