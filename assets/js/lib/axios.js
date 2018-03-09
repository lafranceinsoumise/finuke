import axios from 'axios';

export default axios.create({
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  baseURL: BASE_URL,
});
