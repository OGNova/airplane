import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import sortBy from 'lodash/sortBy';
import {STATS_ENABLED, CONFIG_HISTORY} from 'config';

import { globalState } from '../state';
import Tooltip from './tooltip';
import GuildIcon from './guild_icon';

function partnerOrVerified(guild) {
  if (guild.id == '469566508838682644') {
    return <Tooltip position='right' text='Airplane' trigger={<img src='https://cdn.airplane.gg/static/transparent_airplane.png' height={24} />} />;
  }
  
  if (!guild.features) return;

  let type;
  if (guild.features.indexOf('VERIFIED') > -1) {
    type = 'verified';
  } else if (guild.features.length >= 3) {
    type = 'partner';
  }

  switch (type) {
    case 'verified':
      return <Tooltip position='right' text='Verified' trigger={<img src='https://cdn.discordapp.com/emojis/452956251253374976.png' height={24} />} />;
    case 'partner':
      return <Tooltip position='right' text='Discord Partner' trigger={<img src='https://canary.discordapp.com/assets/33fedf082addb91d88abc272b4b18daa.svg'height={24} />} />
    default:
      break;
  }
  return null;
}

class GuildTableRowActions extends Component {
  render() {
    let parts = [];

    parts.push(
      <Link key='1' to={`/guilds/${this.props.guild.id}`} style={{paddingLeft: '4px'}}>
        <Tooltip position='top' text='Information' trigger={
          <button type='button' className='btn btn-success btn-circle'>
            <i className='fa fa-info'></i>
          </button>
        } />
      </Link>
    );

    parts.push(
      <Link key='2' to={`/guilds/${this.props.guild.id}/config`} style={{paddingLeft: '4px'}}>
        <Tooltip position='top' text='Configuration' trigger={
          <button type='button' className='btn btn-info btn-circle'>
            <i className='fa fa-cog'></i>
          </button>
        } />
      </Link>
    );

    if (CONFIG_HISTORY) {
      parts.push(
        <Link key='3' to={`/guilds/${this.props.guild.id}/config/history`} style={{paddingLeft: '4px'}}>
          <Tooltip position='top' text='Configuration History' trigger={
            <button type='button' className='btn btn-info btn-circle'>
              <i className='fa fa-history'></i>
            </button>
          } />
        </Link>
      );
    }

    if (STATS_ENABLED) {
      parts.push(
        <Link key='4' to={`/guilds/${this.props.guild.id}/stats`} style={{paddingLeft: '4px'}}>
          <Tooltip position='top' text='Statistics' trigger={
            <button type='button' className='btn btn-primary btn-circle'>
              <i className='fas fa-chart-bar'></i>
            </button>
          } />
        </Link>
      );
  }

    parts.push(
      <Link key='5' to={`/guilds/${this.props.guild.id}/infractions`} style={{paddingLeft: '4px'}}>
        <Tooltip position='top' text='Infractions' trigger={
          <button type='button' className='btn btn-warning btn-circle'>
            <i className='fa fa-gavel'></i>
          </button>
        } />
      </Link>
    );

    if (globalState.user && globalState.user.admin) {
      parts.push(
        <a key='6' href='#' style={{paddingLeft: '4px'}} onClick={this.onDelete.bind(this)}>
          <Tooltip position='top' text='Remove Server' trigger={
            <button type='button' className='btn btn-danger btn-circle'>
              <i className='fas fa-trash-alt'></i>
            </button>
          } />
        </a>
      );
    }

    return (
      <div>
        {parts}
      </div>
    );
  }

  onDelete() {
    this.props.guild.delete().then(() => {
      window.location.reload();
    });
  }
}

class GuildTableRowPremiumActions extends Component {
  render(props, state) {
    let parts = [];

    if (globalState.user && globalState.user.admin) {
      parts.push(
        <a key="7" href="#" style={{ paddingLeft: '4px' }} onClick={this.givePremium.bind(this)}>
          <button type="button" className="btn btn-success btn-circle">
            <i className="fa fa-credit-card" aria-hidden="true"></i></button>
        </a>
      )
    }

    if (globalState.user && globalState.user.admin) {
      parts.push(
        <a key="8" href="#" style={{ paddingLeft: '4px' }} onClick={this.cancelPremium.bind(this)}>
          <button type="button" className="btn btn-danger btn-circle">
            <i className="fas fa-trash-alt"></i></button>
        </a>
      )
    }

    return (
      <div>
        {parts}
      </div>
    );
  }

  givePremium() {
    this.props.guild.givePremium().then(() => {
      window.location.reload();
    });
  }

  cancelPremium() {
    this.props.guild.cancelPremium().then(() => {
      window.location.reload()
    });
  }
}

class GuildTableRow extends Component {
  render() {
    return (
      <tr>
        <td>
          <GuildIcon guildID={this.props.guild.id} guildIcon={this.props.guild.icon} scale={26} className='guild-circle' />
          {this.props.guild.name}
        </td>
        <td>{this.props.guild.id}</td>
        <td><GuildTableRowActions guild={this.props.guild} /></td>
        <td><GuildTableRowPremiumActions guild={this.props.guild} /></td>
        <td>{partnerOrVerified(this.props.guild)}</td>
      </tr>
    );
  }
}

class GuildsTable extends Component {
  render() {
    if (!this.props.guilds) {
      return <h3>Loading...</h3>;
    }

    let guilds = sortBy(Object.values(this.props.guilds), (i) => i.id);

    var rows = [];
    guilds.forEach((guild) => {
      if (guild.enabled) {
        rows.push(<GuildTableRow guild={guild} key={guild.id} />);
      }
    });

    return (
      <div className='table-responsive'>
        <table className='table table-hover'>
          <thead>
            <tr>
              <th>Name</th>
              <th>ID</th>
              <th>Actions</th>
              <th>Premium</th>
              <th>Special</th>
            </tr>
          </thead>
          <tbody>
            {rows}
          </tbody>
        </table>
      </div>
    );
  }
}

export default GuildsTable;
