import React, { Component } from 'react';
import Sidebar from './sidebar';
import {globalState} from '../state';
import {withRouter} from 'react-router';
import Tooltip from './tooltip'

class TopLink extends Component {
  render() {
    return (
      <Tooltip position={this.props.ttPosition} text={this.props.text} trigger={
        <a href={this.props.link} target={this.props.external ? '_blank' : ''} rel={this.props.external ? 'noopener' : ''} onClick={this.props.onClick}>
          <i className={this.props.iconClass}></i></a>
      } />
    )
  }
}

class Topbar extends Component {
  constructor() {
    super();
    this.state = {
      showAllGuilds: globalState.showAllGuilds,
      user: globalState.user,
    };

    globalState.events.on('showAllGuilds.set', (value) => this.setState({showAllGuilds: value}));
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
    const expandIcon = this.state.showAllGuilds ? 'fa fa-folder-open' : ' fa fa-folder';

    const user = (
      <Tooltip position='bottom' text="Current User" trigger={
        <span>
          <i className="fas fa-user-alt"></i> {this.state.user.username}
          <span className="darker pad-right">{`#${String(this.state.user.discriminator).padStart(4, "0")}`}
          </span>
        </span>
      } />
    );

    const logout = <TopLink link="#" iconClass="fas fa-sign-out-alt" text="Log out" ttPosition="bottom" onClick={this.onLogoutClicked.bind(this)} />;
    const toggleShown = <TopLink link="#" iconClass={expandIcon} text="Toggle Guilds" ttPosition="bottom" onClick={this.onExpandClicked.bind(this)} />;
    const discord = <TopLink link={globalState.supportServer} iconClass='fab fa-discord' text="Support Server" ttPosition="bottom" external={true} />;
    const dash = <TopLink link='/' iconClass='fas fa-tachometer-alt' text="Dashboard" ttPosition="bottom" />;
    const documentation = <TopLink link={globalState.docsLink} iconClass='fas fa-book' text='Documentation' ttPosition="bottom" external={true} />;

    return(
      <nav className="navbar navbar-default navbar-static-top" role="navigation" style={{marginBottom: 0}}>
        <div className="navbar-header">
          <a className="navbar-brand" href="/">{globalState.name}</a>
        </div>

        <ul className="nav navbar-top-links navbar-right">
          <li>{user}</li>
          <li>{dash}</li>
          <li>{documentation}</li>
          <li>{discord}</li>
          <li>{toggleShown}</li>
          <li>{logout}</li>
        </ul>

        <Sidebar />
      </nav>
    );
  }
}

export default withRouter(Topbar);
