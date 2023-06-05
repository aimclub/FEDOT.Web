import { commonApi } from "../baseURL";
import { IAuth, IToken } from "./authInterface";

export const authAPI = commonApi.injectEndpoints({
  endpoints: (build) => ({
    signin: build.mutation<IToken, IAuth>({
      query: (data) => ({
        url: "/token/get_token",
        method: "POST",
        body: {
          email: data.email,
          password: data.password,
        },
      }),
    }),
    register: build.mutation<{ message: string }, IAuth>({
      query: (data) => ({
        url: "/token/signup",
        method: "POST",
        body: {
          email: data.email,
          password: data.password,
        },
      }),
    }),
  }),
});
