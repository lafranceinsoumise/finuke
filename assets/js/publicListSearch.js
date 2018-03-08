import Cookies from 'js-cookie';
import ReactDOM from "react-dom";
import React from 'react';
import ListSearch from './component/listSearch';

ReactDOM.render(
  (
    <form action="" method="post">
      <input type="hidden" name="csrfmiddlewaretoken" value={Cookies.get('csrftoken')} />
      <ListSearch />
      <div className="input-group">
        <label><input type="checkbox" required />
          &nbsp;J'atteste sur l'honneur de mon identité. Mon vote sera anonyme et confidentiel.</label>
      </div>
      <input type="submit" className="btn btn-primary" value="Je veux voter" />
    </form>
  ),
  document.getElementById('react-root')
);
