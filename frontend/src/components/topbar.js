import React, { Component } from 'react';
import Sidebar from './sidebar';
import {globalState} from '../state';
import {withRouter} from 'react-router';

class Topbar extends Component {
  constructor() {
    super();
    this.state = {
      guilds: null,
      user: globalState.user,
      showAllGuilds: globalState.showAllGuilds,
    };

    globalState.events.on('showAllGuilds.set', (value) => this.setState({showAllGuilds: value}));
  }

  componentDidMount() {
    globalState.getCurrentUser().then((user) => {
      user.getGuilds().then((guilds) => {
        this.setState({guilds});
      });
    });
  }

  onLogoutClicked() {
    globalState.logout().then(() => {
      this.props.history.push('/login');
    });
  }

  onExpandClicked() {
    globalState.showAllGuilds = !globalState.showAllGuilds;
  }

  render() {
    const userIcon = this.state.user.admin ? 'fa fa-shield fa-fw' : 'fa fa-user fa-fw';
    const userTitle = this.state.user.admin ? 'Global Administrator' : 'Dashboard User';
    const expandIcon = this.state.showAllGuilds ? 'fa fa-folder-open fa-fw' : 'fa fa-folder fa-fw';
    const discrim = <span className="text-muted">{"#"+String(this.state.user.discriminator).padStart(4, "0")}</span>

    let buttonsList = [
      <li key="user"><a title={userTitle} className="no-hover"><i className={userIcon}></i>&nbsp;{this.state.user.username}{discrim}</a></li>
    ];
    if (this.state.guilds && Object.keys(this.state.guilds).length > 10) {
      buttonsList.push(
        <li key="expand"><a title="Expand" onClick={this.onExpandClicked.bind(this)}><i className={expandIcon}></i></a></li>
      )
    }
    buttonsList.push(
      <li key="logout"><a title="Logout" onClick={this.onLogoutClicked.bind(this)}><i className="fa fa-sign-out fa-fw"></i></a></li>
    )

    return(
      <nav className="navbar navbar-default navbar-static-top" role="navigation" style={{marginBottom: 0}}>
        <div className="navbar-header">
          <a className="navbar-brand">Airplane</a>
        </div>

        <ul className="nav navbar-top-links navbar-right">
          {buttonsList}
        </ul>

        <Sidebar />
      </nav>
    );
    }
  }

  export default withRouter(Topbar);