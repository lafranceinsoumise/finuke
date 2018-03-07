import Cookies from 'js-cookie';
import ReactDOM from "react-dom";
import React from 'react';
import ListSearch from './component/listSearch';

ReactDOM.render(
  (
    <form action="" method="post">
      <input type="hidden" name="csrfmiddlewaretoken" value={Cookies.get('csrftoken')} />
      <ListSearch />
      <input type="submit" className="btn btn-primary" value="Je veux voter" />
    </form>
  ),
  document.getElementById('react-root')
);