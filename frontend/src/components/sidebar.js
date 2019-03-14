import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import sortBy from 'lodash/sortBy';

import {globalState} from '../state';
import {STATS_ENABLED, CONFIG_HISTORY} from 'config';
import GuildIcon from './guild_icon';
import Tooltip from './tooltip'

class SidebarLink extends Component {
  render () {
    const iconClass = `fas fa-${this.props.icon} sidebar-icon`;
    return (
      <li className={this.props.activePage && this.props.activePage === this.props.text.toLowerCase() ? 'active' : undefined}>
        <Tooltip position='right-end' text={this.props.text} interactive={false} distance={200} trigger={
          <Link to={this.props.to}>
            <i className={iconClass}></i>
          </Link>
        } />
      </li>
    );
  }
}


class GuildLinks extends Component {
  render() {
    let links = [];

    if (this.props.active) {
      let activePage = '';
      switch (this.props.page) {
        case String(this.props.guild.id):
          activePage = 'info';
          break;
        default:
          activePage = this.props.page;
          break;
      }

      links.push(
        <SidebarLink icon='info' to={'/guilds/' + this.props.guild.id} activePage={activePage} text='Info' key='info' />
      );

      links.push(
        <SidebarLink icon='cog' to={'/guilds/' + this.props.guild.id + '/config'} activePage={activePage} text='Config' key='config' />
      );

      if (CONFIG_HISTORY) {
        links.push(
          <SidebarLink icon='history' to={'/guilds/' + this.props.guild.id + '/config/history'} activePage={activePage} text='History' key='history' />
        );
      }

      links.push(
        <SidebarLink icon='gavel' to={'/guilds/' + this.props.guild.id + '/infractions'} activePage={activePage} text='Infractions' key='infractions' />
      );

      if (STATS_ENABLED) {
        links.push(
          <SidebarLink icon='chart-bar' to={'/guilds/' + this.props.guild.id + '/stats'} activePage={activePage} text='Stats' key='stats' />
        );
      }
    }
    return (
      <li className={this.props.active ? 'active-guild active' : ''}>
        <Link to={'/guilds/' + this.props.guild.id}>
          <Tooltip position='right-end' text={this.props.guild.name}interactive={false} trigger={
            <GuildIcon guildID={this.props.guild.id} guildIcon={this.props.guild.icon} className='guild-circle' scale={40} />
          } />
        </Link>
        <ul className="nav nav-second-level collapse in">
          {links}
        </ul>
      </li>
    );
  }
}


class Sidebar extends Component {
  constructor() {
    super();

    this.state = {
      guilds: null,
      currentGuildID: globalState.currentGuild ? globalState.currentGuild.id : null,
      showAllGuilds: globalState.showAllGuilds,
    };

    globalState.events.on('showAllGuilds.set', (value) => this.setState({showAllGuilds: value}));

    globalState.getCurrentUser().then((user) => {
      user.getGuilds().then((guilds) => {
        this.setState({guilds});
      });
    });

    globalState.events.on('currentGuild.set', (guild) => {
      this.setState({currentGuildID: guild ? guild.id : null});
    });
  }

  render() {
    let sidebarLinks = [];

    if (this.state.guilds) {
      const guilds = sortBy(Object.values(this.state.guilds), (i) => i.name);

      for (let guild of guilds) {
        // Only show the active guild for users with a lot of them
        if (
          !this.state.showAllGuilds &&
          Object.keys(this.state.guilds).length > 10 &&
          guild.id != this.state.currentGuildID
        ) continue;
        sidebarLinks.push(<GuildLinks guild={guild} active={guild.id == this.state.currentGuildID} page={window.location.href.split('/').pop()} key={guild.id}/>);
      }
    }

    return (
      <div className="navbar-default sidebar" role="navigation">
        <div className="sidebar-nav navbar-collapse">
          <ul className="nav in" id="side-menu">
            {sidebarLinks}
          </ul>
        </div>
      </div>
    );
  }
}

export default Sidebar;