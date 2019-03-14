import React, { Component } from 'react';

class GuildIcon extends Component {
  render() {
    if (this.props.guildIcon) {
      const source = `https://cdn.discordapp.com/icons/${this.props.guildID}/${this.props.guildIcon}.png`;
      return (
            <img src={source} height={this.props.scale || 128} className={this.props.className} alt="No Icon" />
        );
    } else {
      const iStyle = {
        height: this.props.scale,
        width: this.props.scale,
        fontSize: this.props.scale,
        verticalAlign: 'middle',
      };
      const classes = `fas fa-minus-circle ${this.props.className}`
      return <i className={classes} style={iStyle}></i>;
    }
  }
}

export default GuildIcon;
